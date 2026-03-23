"""Stage F: Deduplication — find and resolve duplicate cards."""

from __future__ import annotations

import json
import logging
import re
from collections import Counter

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_f import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import DedupOutput, schema_for

logger = logging.getLogger(__name__)

# Legacy threshold kept for backward compatibility (unused internally now)
OVERLAP_THRESHOLD = 0.80

# Two-tier similarity thresholds
TOKEN_OVERLAP_THRESHOLD = 0.70
CHAR_NGRAM_THRESHOLD = 0.60
CHAR_NGRAM_AUTO_RESOLVE_THRESHOLD = 0.90


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\w+", text.lower())


def _token_overlap(a: str, b: str) -> float:
    """Compute Jaccard-like token overlap between two strings."""
    tokens_a = Counter(_tokenize(a))
    tokens_b = Counter(_tokenize(b))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = sum((tokens_a & tokens_b).values())
    union = sum((tokens_a | tokens_b).values())
    return intersection / union if union > 0 else 0.0


def _char_ngram_overlap(text_a: str, text_b: str, n: int = 3) -> float:
    """Character n-gram Jaccard similarity (order-invariant).

    Computes similarity based on overlapping character n-grams, which catches
    paraphrased duplicates better than word-level token overlap.
    """
    a_lower = text_a.lower()
    b_lower = text_b.lower()
    if len(a_lower) < n or len(b_lower) < n:
        return 0.0
    ngrams_a = Counter(a_lower[i : i + n] for i in range(len(a_lower) - n + 1))
    ngrams_b = Counter(b_lower[i : i + n] for i in range(len(b_lower) - n + 1))
    intersection = sum((ngrams_a & ngrams_b).values())
    union = sum((ngrams_a | ngrams_b).values())
    return intersection / union if union > 0 else 0.0


def _combined_similarity(front_a: str, front_b: str) -> tuple[float, float]:
    """Compute both token and char-ngram similarity for a pair of fronts.

    Returns (token_overlap, char_ngram_overlap).
    """
    token_sim = _token_overlap(front_a, front_b)
    ngram_sim = _char_ngram_overlap(front_a, front_b)
    return token_sim, ngram_sim


def find_duplicate_pairs(cards: list[dict]) -> list[tuple[int, int, float]]:
    """Find pairs of cards with high similarity using two-tier detection.

    Uses both token Jaccard and character 3-gram Jaccard to catch
    paraphrased duplicates that word-level overlap misses.

    Returns list of (index_a, index_b, best_overlap_score) tuples.
    Only considers non-suppressed cards.
    """
    pairs = []
    active = [(i, c) for i, c in enumerate(cards) if not c.get("suppressed")]

    for ai in range(len(active)):
        for bi in range(ai + 1, len(active)):
            idx_a, card_a = active[ai]
            idx_b, card_b = active[bi]
            # Two-tier similarity: token overlap OR char n-gram overlap
            token_sim, ngram_sim = _combined_similarity(card_a["front"], card_b["front"])
            if token_sim >= TOKEN_OVERLAP_THRESHOLD or ngram_sim >= CHAR_NGRAM_THRESHOLD:
                # Report the higher of the two as the overlap score
                best_score = max(token_sim, ngram_sim)
                pairs.append((idx_a, idx_b, best_score))

    return pairs


def resolve_duplicates(
    cards: list[dict],
    pairs: list[tuple[int, int, float]],
) -> list[dict]:
    """Resolve duplicate pairs. Auto-resolves high-confidence pairs; uses LLM for borderline.

    High-confidence pairs (char n-gram >= 0.90) are auto-resolved as keep_first
    without an LLM call. Borderline pairs are sent to the LLM for judgment.
    """
    if not pairs:
        return []

    decisions: list[dict] = []
    llm_pairs: list[tuple[int, int, int, float]] = []  # (pair_index, idx_a, idx_b, score)

    for i, (idx_a, idx_b, score) in enumerate(pairs):
        # Check if this pair qualifies for auto-resolution
        _token_sim, ngram_sim = _combined_similarity(cards[idx_a]["front"], cards[idx_b]["front"])
        if ngram_sim >= CHAR_NGRAM_AUTO_RESOLVE_THRESHOLD:
            # Auto-resolve: keep the first card
            decisions.append(
                {
                    "pair_index": i,
                    "action": "keep_first",
                    "merged_front": "",
                    "merged_back": "",
                }
            )
            logger.debug("Auto-resolved pair %d (ngram=%.2f): keep_first", i, ngram_sim)
        else:
            llm_pairs.append((i, idx_a, idx_b, score))

    # Send borderline pairs to LLM
    if llm_pairs:
        pairs_for_prompt = []
        for pair_index, idx_a, idx_b, score in llm_pairs:
            pairs_for_prompt.append(
                {
                    "pair_index": pair_index,
                    "overlap_score": round(score, 2),
                    "card_a": {
                        "index": idx_a,
                        "front": cards[idx_a]["front"],
                        "back": cards[idx_a]["back"],
                    },
                    "card_b": {
                        "index": idx_b,
                        "front": cards[idx_b]["front"],
                        "back": cards[idx_b]["back"],
                    },
                }
            )

        user = USER_TEMPLATE.format(pairs_json=json.dumps(pairs_for_prompt, indent=2))
        result = structured_call(
            system=SYSTEM,
            user=user,
            tool_name="resolve_duplicates",
            tool_schema=schema_for(DedupOutput),
            model=settings.model_stage_f,
            max_tokens=1024,
        )
        output = DedupOutput.model_validate(result)
        decisions.extend(r.model_dump() for r in output.results)

    return decisions


def apply_dedup(
    cards: list[dict],
    pairs: list[tuple[int, int, float]],
    decisions: list[dict],
) -> list[dict]:
    """Apply dedup decisions to cards.

    Marks losers as suppressed with duplicate_of set.
    For merge, replaces first card's text and suppresses second.
    """
    decision_map = {d["pair_index"]: d for d in decisions}

    for i, (idx_a, idx_b, _score) in enumerate(pairs):
        decision = decision_map.get(i)
        if not decision:
            continue

        action = decision["action"]

        if action == "keep_first":
            cards[idx_b]["suppressed"] = True
            cards[idx_b]["duplicate_of"] = idx_a
        elif action == "keep_second":
            cards[idx_a]["suppressed"] = True
            cards[idx_a]["duplicate_of"] = idx_b
        elif action == "merge":
            if decision.get("merged_front"):
                cards[idx_a]["front"] = decision["merged_front"]
            if decision.get("merged_back"):
                cards[idx_a]["back"] = decision["merged_back"]
            cards[idx_b]["suppressed"] = True
            cards[idx_b]["duplicate_of"] = idx_a
        # keep_both: do nothing

    return cards
