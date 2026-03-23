"""Stage B: Merge and deduplicate concepts within a section via LLM."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_b import USER_TEMPLATE, build_system_prompt
from ankithis_api.llm.schemas import ConceptMergeOutput, schema_for

logger = logging.getLogger(__name__)


def merge_concepts(
    concepts: list[dict],
    section_title: str | None = None,
    study_goal: str = "Master the key concepts in this material",
    content_type: str | None = None,
) -> list[dict]:
    """Merge and deduplicate concepts for a section. Returns merged concept dicts."""
    if not concepts:
        return []

    system = build_system_prompt(content_type=content_type)

    user = USER_TEMPLATE.format(
        study_goal=study_goal,
        section_title=section_title or "Untitled Section",
        concepts_json=json.dumps(concepts, indent=2),
    )
    result = structured_call(
        system=system,
        user=user,
        tool_name="merge_concepts",
        tool_schema=schema_for(ConceptMergeOutput),
        model=settings.model_stage_b,
        max_tokens=2048,
    )
    output = ConceptMergeOutput.model_validate(result)
    return [c.model_dump() for c in output.concepts]


def merge_concepts_batch(
    sections_concepts: list[tuple[str, list[dict]]],
    study_goal: str = "Master the key concepts",
    content_type: str | None = None,
) -> list[dict]:
    """Merge concepts from multiple sections in a single LLM call.

    sections_concepts: list of (section_title, concepts_list) tuples.
    Returns flat list of merged concept dicts.
    """
    if not sections_concepts:
        return []

    # Build concatenated section blocks with delimiters
    section_blocks: list[str] = []
    for title, concepts in sections_concepts:
        block = f"--- SECTION: {title} ---\n{json.dumps(concepts, indent=2)}"
        section_blocks.append(block)
    all_sections_text = "\n\n".join(section_blocks)

    system = build_system_prompt(content_type=content_type)

    user = (
        f"Merge duplicate concepts within each section below. "
        f"The student's study goal is: {study_goal}\n\n"
        f"{all_sections_text}\n\n"
        f"Return the merged, deduplicated concept list."
    )

    result = structured_call(
        system=system,
        user=user,
        tool_name="merge_concepts",
        tool_schema=schema_for(ConceptMergeOutput),
        model=settings.model_stage_b,
        max_tokens=2048,
    )
    output = ConceptMergeOutput.model_validate(result)
    return [c.model_dump() for c in output.concepts]
