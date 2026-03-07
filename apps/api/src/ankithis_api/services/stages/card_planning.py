"""Stage C: Plan cards — decide count, type, and direction for each concept."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_c import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import CardPlanOutput, schema_for
from ankithis_api.models.enums import CardStyle, DeckSize

logger = logging.getLogger(__name__)

DECK_SIZE_TARGETS = {
    DeckSize.SMALL: (30, 50),
    DeckSize.MEDIUM: (80, 150),
    DeckSize.LARGE: (200, 300),
}

CARD_STYLE_DESC = {
    CardStyle.CLOZE_HEAVY: "Strongly prefer cloze cards (70-80% cloze, rest basic)",
    CardStyle.QA_HEAVY: "Strongly prefer basic Q&A cards (70-80% basic, rest cloze)",
    CardStyle.BALANCED: "Balance evenly between cloze and basic cards (50/50)",
}


def plan_cards(
    concepts: list[dict],
    deck_size: DeckSize = DeckSize.MEDIUM,
    card_style: CardStyle = CardStyle.CLOZE_HEAVY,
    study_goal: str = "Master the key concepts in this material",
) -> list[dict]:
    """Plan cards for a set of merged concepts. Returns card plan dicts."""
    if not concepts:
        return []

    low, high = DECK_SIZE_TARGETS[deck_size]
    target = (low + high) // 2
    style_desc = CARD_STYLE_DESC[card_style]

    system = SYSTEM.format(card_style=style_desc, target_cards=target)
    user = USER_TEMPLATE.format(
        target_cards=target,
        card_style=style_desc,
        study_goal=study_goal,
        concepts_json=json.dumps(concepts, indent=2),
    )
    result = structured_call(
        system=system,
        user=user,
        tool_name="plan_cards",
        tool_schema=schema_for(CardPlanOutput),
        model=settings.model_stage_c,
    )
    output = CardPlanOutput.model_validate(result)
    return [c.model_dump() for c in output.cards]
