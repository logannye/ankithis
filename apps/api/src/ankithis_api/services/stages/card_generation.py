"""Stage D: Generate actual flashcard text from card plans."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_d import SYSTEM, USER_TEMPLATE, build_system_prompt
from ankithis_api.llm.schemas import CardGenerationOutput, schema_for

logger = logging.getLogger(__name__)

# Process plans in batches to stay within context limits
BATCH_SIZE = 20


def generate_cards(
    plans: list[dict],
    source_text: str,
    study_goal: str = "Master the key concepts in this material",
    content_profile: dict | None = None,
) -> list[dict]:
    """Generate flashcard text from card plans. Returns generated card dicts."""
    if not plans:
        return []

    # Build adapted system prompt from content profile
    difficulty = None
    special_considerations = None
    if content_profile:
        difficulty = content_profile.get("difficulty")
        special_considerations = content_profile.get("special_considerations")

    system = build_system_prompt(
        difficulty=difficulty,
        special_considerations=special_considerations,
    )

    all_cards: list[dict] = []

    for i in range(0, len(plans), BATCH_SIZE):
        batch = plans[i : i + BATCH_SIZE]
        # Truncate source text if very long to stay in context
        truncated_source = source_text[:8000] if len(source_text) > 8000 else source_text

        user = USER_TEMPLATE.format(
            study_goal=study_goal,
            source_text=truncated_source,
            plans_json=json.dumps(batch, indent=2),
        )
        result = structured_call(
            system=system,
            user=user,
            tool_name="generate_cards",
            tool_schema=schema_for(CardGenerationOutput),
            model=settings.model_stage_d,
        )
        output = CardGenerationOutput.model_validate(result)
        all_cards.extend(c.model_dump() for c in output.cards)

    return all_cards
