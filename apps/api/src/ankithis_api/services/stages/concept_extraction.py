"""Stage A: Extract concepts from each text chunk via LLM."""

from __future__ import annotations

import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_a import build_system_prompt, build_user_prompt
from ankithis_api.llm.schemas import ConceptExtractionOutput, schema_for

logger = logging.getLogger(__name__)


def extract_concepts(
    chunk_text: str,
    study_goal: str = "Master the key concepts in this material",
    content_type: str | None = None,
    difficulty: str | None = None,
    pedagogical_function: str | None = None,
    visual_context: str | None = None,
) -> list[dict]:
    """Extract concepts from a single chunk. Returns list of concept dicts."""
    system = build_system_prompt(content_type, difficulty, pedagogical_function)
    user = build_user_prompt(chunk_text, study_goal, visual_context)
    result = structured_call(
        system=system,
        user=user,
        tool_name="extract_concepts",
        tool_schema=schema_for(ConceptExtractionOutput),
        model=settings.model_stage_a,
    )
    output = ConceptExtractionOutput.model_validate(result)
    return [c.model_dump() for c in output.concepts]
