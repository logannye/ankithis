"""Stage 0: Classify document content to produce a ContentProfile."""

from __future__ import annotations

import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_0 import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import ClassificationOutput, schema_for
from ankithis_api.services.parser import ParsedSection

logger = logging.getLogger(__name__)

DEFAULT_PROFILE: dict = {
    "content_type": "general_article",
    "domain": "general",
    "difficulty": "intermediate",
    "information_density": "moderate",
    "structure_quality": "semi_structured",
    "primary_knowledge_type": "mixed",
    "recommended_cloze_ratio": 0.5,
    "recommended_qa_ratio": 0.5,
    "special_considerations": [],
}


def _build_sample(
    sections: list[ParsedSection],
) -> tuple[str, str, str]:
    """Extract headings, opening text, and closing text for classification."""
    headings = "\n".join(f"{'#' * s.level} {s.title}" for s in sections if s.title)

    # Opening: first ~2000 words
    all_text = "\n\n".join(s.text for s in sections)
    words = all_text.split()
    opening = " ".join(words[:2000])

    # Closing: last ~500 words
    closing = " ".join(words[-500:]) if len(words) > 500 else ""

    return headings, opening, closing


def _safe_classify(headings: str, opening: str, closing: str) -> dict:
    """Call LLM for classification, return DEFAULT_PROFILE on any failure."""
    if not opening.strip():
        return dict(DEFAULT_PROFILE)

    try:
        user = USER_TEMPLATE.format(
            headings=headings or "(no headings detected)",
            opening_text=opening[:12000],
            closing_text=closing[:3000],
        )
        result = structured_call(
            system=SYSTEM,
            user=user,
            tool_name="classify_content",
            tool_schema=schema_for(ClassificationOutput),
            model=settings.bedrock_model,
            max_tokens=512,
        )
        output = ClassificationOutput.model_validate(result)
        return output.model_dump()
    except Exception:
        logger.warning("Content classification failed, using defaults", exc_info=True)
        return dict(DEFAULT_PROFILE)


def classify_document(sections: list[ParsedSection]) -> dict:
    """Run Stage 0 classification on parsed sections. Returns profile dict."""
    headings, opening, closing = _build_sample(sections)
    return _safe_classify(headings, opening, closing)
