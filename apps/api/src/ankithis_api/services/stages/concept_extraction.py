"""Stage A: Extract concepts from each text chunk via LLM."""

from __future__ import annotations

import logging

from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_a import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import ConceptExtractionOutput, schema_for

logger = logging.getLogger(__name__)


def extract_concepts(
    chunk_text: str,
    study_goal: str = "Master the key concepts in this material",
) -> list[dict]:
    """Extract concepts from a single chunk. Returns list of concept dicts."""
    user = USER_TEMPLATE.format(chunk_text=chunk_text, study_goal=study_goal)
    result = structured_call(
        system=SYSTEM,
        user=user,
        tool_name="extract_concepts",
        tool_schema=schema_for(ConceptExtractionOutput),
    )
    output = ConceptExtractionOutput.model_validate(result)
    return [c.model_dump() for c in output.concepts]
