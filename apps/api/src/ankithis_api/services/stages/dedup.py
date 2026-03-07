"""Stage F: Deduplication — find and resolve duplicate cards."""

from __future__ import annotations

import json
import logging
import re
from collections import Counter

from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_f import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import DedupOutput, schema_for

logger = logging.getLogger(__name__)

OVERLAP_THRESHOLD = 0.80


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


def find_duplicate_pairs(cards: list[dict]) -> list[tuple[int, int, float]]:
    """Find pairs of cards with high token overlap.

    Returns list of (index_a, index_b, overlap_score) tuples.
    Only considers non-suppressed cards.
    """
    pairs = []
    active = [(i, c) for i, c in enumerate(cards) if not c.get("suppressed")]

    for ai in range(len(active)):
        for bi in range(ai + 1, len(active)):
            idx_a, card_a = active[ai]
            idx_b, card_b = active[bi]
            # Compare front text
            overlap = _token_overlap(card_a["front"], card_b["front"])
            if overlap >= OVERLAP_THRESHOLD:
                pairs.append((idx_a, idx_b, overlap))

    return pairs


def resolve_duplicates(
    cards: list[dict],
    pairs: list[tuple[int, int, float]],
) -> list[dict]:
    """Use LLM to resolve duplicate pairs. Returns dedup decisions."""
    if not pairs:
        return []

    pairs_for_prompt = []
    for i, (idx_a, idx_b, score) in enumerate(pairs):
        pairs_for_prompt.append({
            "pair_index": i,
            "overlap_score": round(score, 2),
            "card_a": {"index": idx_a, "front": cards[idx_a]["front"], "back": cards[idx_a]["back"]},
            "card_b": {"index": idx_b, "front": cards[idx_b]["front"], "back": cards[idx_b]["back"]},
        })

    user = USER_TEMPLATE.format(pairs_json=json.dumps(pairs_for_prompt, indent=2))
    result = structured_call(
        system=SYSTEM,
        user=user,
        tool_name="resolve_duplicates",
        tool_schema=schema_for(DedupOutput),
    )
    output = DedupOutput.model_validate(result)
    return [r.model_dump() for r in output.results]


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
