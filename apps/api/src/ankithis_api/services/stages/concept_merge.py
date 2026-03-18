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
    )
    output = ConceptMergeOutput.model_validate(result)
    return [c.model_dump() for c in output.concepts]
