"""Stage D: Generate actual flashcard text from card plans."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_d import USER_TEMPLATE, build_system_prompt
from ankithis_api.llm.schemas import CardGenerationOutput, schema_for

logger = logging.getLogger(__name__)

# Process plans in batches to stay within context limits
BATCH_SIZE = 20


def _build_batch_context(
    batch: list[dict],
    source_text: str,
    section_text_map: dict[str, str] | None,
    concept_to_section: dict[str, str] | None,
) -> str:
    """Build source context for a batch of plans.

    When section maps are available, returns only the sections relevant to this
    batch's concepts (up to 12 000 chars). Falls back to the first 8 000 chars
    of the full document otherwise.
    """
    if section_text_map and concept_to_section:
        relevant_sections: set[str] = set()
        for plan in batch:
            concept_name = plan.get("concept_name", "")
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


def generate_cards(
    plans: list[dict],
    source_text: str,
    study_goal: str = "Master the key concepts in this material",
    content_profile: dict | None = None,
    section_text_map: dict[str, str] | None = None,
    concept_to_section: dict[str, str] | None = None,
) -> list[dict]:
    """Generate flashcard text from card plans. Returns generated card dicts.

    When *section_text_map* and *concept_to_section* are provided, each batch
    receives only the source sections that are relevant to its concepts instead
    of a fixed 8 000-char prefix of the entire document.
    """
    if not plans:
        return []

    # Build adapted system prompt from content profile
    difficulty = None
    special_considerations = None
    knowledge_type = None
    if content_profile:
        difficulty = content_profile.get("difficulty")
        special_considerations = content_profile.get("special_considerations")
        knowledge_type = content_profile.get("primary_knowledge_type")

    # Collect distinct Bloom's levels from the card plans
    bloom_levels: list[str] = []
    seen_blooms: set[str] = set()
    for plan in plans:
        bl = plan.get("bloom_level")
        if bl and bl not in seen_blooms:
            seen_blooms.add(bl)
            bloom_levels.append(bl)

    system = build_system_prompt(
        difficulty=difficulty,
        special_considerations=special_considerations,
        knowledge_type=knowledge_type,
        bloom_levels=bloom_levels or None,
    )

    all_cards: list[dict] = []

    for i in range(0, len(plans), BATCH_SIZE):
        batch = plans[i : i + BATCH_SIZE]

        context = _build_batch_context(batch, source_text, section_text_map, concept_to_section)

        user = USER_TEMPLATE.format(
            study_goal=study_goal,
            source_text=context,
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
