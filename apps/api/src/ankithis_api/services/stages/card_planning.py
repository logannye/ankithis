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

# Cards per 1,000 words — scales with document length
CARDS_PER_1K_WORDS = {
    DeckSize.SMALL: 5,    # key concepts only
    DeckSize.MEDIUM: 12,  # solid coverage
    DeckSize.LARGE: 22,   # deep, thorough coverage
}

MIN_CARDS = 5
MAX_CARDS = 300

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
    total_words: int = 0,
) -> list[dict]:
    """Plan cards for a set of merged concepts. Returns card plan dicts."""
    if not concepts:
        return []

    density = CARDS_PER_1K_WORDS[deck_size]
    target = max(MIN_CARDS, min(MAX_CARDS, round(total_words / 1000 * density)))
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
