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
    knowledge_type: str | None = None,
) -> list[dict]:
    """Extract concepts from a single chunk. Returns list of concept dicts."""
    system = build_system_prompt(content_type, difficulty, pedagogical_function, knowledge_type)
    user = build_user_prompt(chunk_text, study_goal, visual_context)
    result = structured_call(
        system=system,
        user=user,
        tool_name="extract_concepts",
        tool_schema=schema_for(ConceptExtractionOutput),
        model=settings.model_stage_a,
        max_tokens=2048,
    )
    output = ConceptExtractionOutput.model_validate(result)
    return [c.model_dump() for c in output.concepts]


def extract_concepts_batch(
    chunks: list[dict],
    study_goal: str = "Master the key concepts in this material",
    content_type: str | None = None,
    difficulty: str | None = None,
    pedagogical_function: str | None = None,
    knowledge_type: str | None = None,
) -> list[dict]:
    """Extract concepts from multiple chunks in a single LLM call.

    Each chunk dict has keys: text, visual_context (optional).
    Returns flat list of concept dicts from all chunks combined.
    """
    if not chunks:
        return []

    # Build combined chunk text with clear delimiters
    parts = []
    for i, chunk in enumerate(chunks):
        section = f"--- CHUNK {i + 1} ---\n{chunk['text']}"
        if chunk.get("visual_context"):
            section += f"\n\nVisual context (from video/diagrams):\n{chunk['visual_context']}"
        parts.append(section)
    combined_text = "\n\n".join(parts)

    system = build_system_prompt(content_type, difficulty, pedagogical_function, knowledge_type)
    user = (
        f"Extract the key educational concepts from each labeled chunk below. "
        f"The student's study goal is: {study_goal}\n\n"
        f"{combined_text}\n\n"
        f"Extract all concepts worth making flashcards about."
    )

    result = structured_call(
        system=system,
        user=user,
        tool_name="extract_concepts",
        tool_schema=schema_for(ConceptExtractionOutput),
        model=settings.model_stage_a,
        max_tokens=2048,
    )
    output = ConceptExtractionOutput.model_validate(result)
    return [c.model_dump() for c in output.concepts]
