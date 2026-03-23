"""Stage E: Critique — evaluate card quality, rewrite if needed."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_e import USER_TEMPLATE, build_system_prompt
from ankithis_api.llm.schemas import CritiqueOutput, schema_for

logger = logging.getLogger(__name__)

BATCH_SIZE = 25


def _build_critique_context(
    batch_start: int,
    batch_end: int,
    source_text: str,
    plans: list[dict] | None,
    section_text_map: dict[str, str] | None,
    concept_to_section: dict[str, str] | None,
) -> str:
    """Build source context for a critique batch.

    Uses the card plans to look up which sections the cards in
    [batch_start, batch_end) belong to and returns relevant section text
    (up to 12 000 chars). Falls back to the first 8 000 chars of the full
    document when section maps are unavailable.
    """
    if section_text_map and concept_to_section and plans:
        relevant_sections: set[str] = set()
        for idx in range(batch_start, min(batch_end, len(plans))):
            concept_name = plans[idx].get("concept_name", "")
            section_id = concept_to_section.get(concept_name)
            if section_id:
                relevant_sections.add(section_id)

        if relevant_sections:
            context = "\n\n---\n\n".join(
                section_text_map[sid] for sid in relevant_sections if sid in section_text_map
            )
            return context[:12000] if len(context) > 12000 else context

    # Fallback: truncated full document
    return source_text[:8000] if len(source_text) > 8000 else source_text


def critique_cards(
    cards: list[dict],
    source_text: str,
    content_type: str | None = None,
    section_text_map: dict[str, str] | None = None,
    concept_to_section: dict[str, str] | None = None,
    plans: list[dict] | None = None,
) -> list[dict]:
    """Critique cards and return verdict for each.

    Returns list of dicts with keys: card_index, verdict, front, back, reason.
    Rewritten cards get one additional retry.

    When *section_text_map*, *concept_to_section*, and *plans* are provided,
    each batch receives only the source sections relevant to its cards instead
    of a fixed 8 000-char prefix of the entire document.
    """
    if not cards:
        return []

    # Detect if any card plans include Bloom's levels
    has_bloom = bool(plans and any(p.get("bloom_level") for p in plans))

    system = build_system_prompt(content_type=content_type, has_bloom_levels=has_bloom)

    all_reviews: list[dict] = []

    for batch_start in range(0, len(cards), BATCH_SIZE):
        batch = cards[batch_start : batch_start + BATCH_SIZE]
        # Format cards for the prompt, including bloom_level when available
        cards_for_prompt = []
        for i, c in enumerate(batch):
            entry: dict = {
                "index": i,
                "front": c["front"],
                "back": c["back"],
                "card_type": c["card_type"],
            }
            # Attach bloom_level from the corresponding plan so the critique
            # can verify cognitive-level alignment
            plan_idx = batch_start + i
            if plans and plan_idx < len(plans):
                bl = plans[plan_idx].get("bloom_level")
                if bl:
                    entry["bloom_level"] = bl
            cards_for_prompt.append(entry)

        context = _build_critique_context(
            batch_start,
            batch_start + len(batch),
            source_text,
            plans,
            section_text_map,
            concept_to_section,
        )
        user = USER_TEMPLATE.format(
            source_text=context,
            cards_json=json.dumps(cards_for_prompt, indent=2),
        )
        result = structured_call(
            system=system,
            user=user,
            tool_name="critique_cards",
            tool_schema=schema_for(CritiqueOutput),
            model=settings.model_stage_e,
            max_tokens=3072,
        )
        output = CritiqueOutput.model_validate(result)

        # Adjust indices for batching and collect
        for review in output.reviews:
            review_dict = review.model_dump()
            review_dict["card_index"] = review.card_index + batch_start
            all_reviews.append(review_dict)

    return all_reviews


def apply_critique(cards: list[dict], reviews: list[dict]) -> list[dict]:
    """Apply critique verdicts to cards.

    Returns updated cards list with critique_verdict set.
    Cards with 'suppress' verdict get suppressed=True.
    Cards with 'rewrite' verdict get their text replaced.
    """
    review_map = {r["card_index"]: r for r in reviews}
    result = []

    for i, card in enumerate(cards):
        review = review_map.get(i)
        if not review:
            card["critique_verdict"] = "pass"
            result.append(card)
            continue

        verdict = review["verdict"]
        card["critique_verdict"] = verdict

        if verdict == "suppress":
            card["suppressed"] = True
        elif verdict == "rewrite":
            if review.get("front"):
                card["front"] = review["front"]
            if review.get("back"):
                card["back"] = review["back"]

        result.append(card)

    return result
