"""Stage E: Critique — evaluate card quality, rewrite if needed."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_e import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import CritiqueOutput, schema_for

logger = logging.getLogger(__name__)

BATCH_SIZE = 25


def critique_cards(
    cards: list[dict],
    source_text: str,
) -> list[dict]:
    """Critique cards and return verdict for each.

    Returns list of dicts with keys: card_index, verdict, front, back, reason.
    Rewritten cards get one additional retry.
    """
    if not cards:
        return []

    all_reviews: list[dict] = []

    for batch_start in range(0, len(cards), BATCH_SIZE):
        batch = cards[batch_start : batch_start + BATCH_SIZE]
        # Format cards for the prompt
        cards_for_prompt = [
            {"index": i, "front": c["front"], "back": c["back"], "card_type": c["card_type"]}
            for i, c in enumerate(batch)
        ]

        truncated_source = source_text[:8000] if len(source_text) > 8000 else source_text
        user = USER_TEMPLATE.format(
            source_text=truncated_source,
            cards_json=json.dumps(cards_for_prompt, indent=2),
        )
        result = structured_call(
            system=SYSTEM,
            user=user,
            tool_name="critique_cards",
            tool_schema=schema_for(CritiqueOutput),
            model=settings.model_stage_e,
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
