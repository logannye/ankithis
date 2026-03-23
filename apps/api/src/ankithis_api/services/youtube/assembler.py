"""Assemble YouTube sections + visual context into ParsedSection format."""

from __future__ import annotations

import logging
import re

from ankithis_api.services.parser import ParsedSection

logger = logging.getLogger(__name__)


def assemble_chunks(
    sections: list[dict],
    frame_annotations: list[dict] | None = None,
) -> list[tuple[ParsedSection, list[str]]]:
    """Convert YouTube sections into ParsedSection objects with visual context.

    Args:
        sections: [{title, start_time, end_time, text}]
        frame_annotations: [{timestamp, visual_content, content_type, additive_value}]

    Returns:
        List of (ParsedSection, visual_contexts) tuples.
        visual_contexts is a list of visual content strings for chunks in that section.
    """
    if not sections:
        return []

    annotations = frame_annotations or []

    result = []
    for section in sections:
        start = section.get("start_time", 0)
        end = section.get("end_time", float("inf"))

        # Find visual annotations within this section's time range
        section_visuals = [
            ann["visual_content"]
            for ann in annotations
            if start <= ann.get("timestamp", 0) < end and ann.get("additive_value") != "none"
        ]

        # Build ParsedSection
        text = section.get("text", "")
        paragraphs = _split_into_paragraphs(text)

        parsed = ParsedSection(
            title=section.get("title"),
            level=1,
            paragraphs=paragraphs,
        )

        # Combine visual context into a single string for the chunk
        visual_context = "\n".join(section_visuals) if section_visuals else None

        result.append((parsed, [visual_context] if visual_context else []))

    return result


def _split_into_paragraphs(text: str, target_words: int = 150) -> list[str]:
    """Split continuous transcript text into paragraph-like chunks.

    Transcripts are often a wall of text. Split at sentence boundaries
    to create readable paragraphs of ~150 words each.
    """
    if not text:
        return []

    # Split into sentences (rough heuristic)
    sentences = re.split(r"(?<=[.!?])\s+", text)

    paragraphs = []
    current: list[str] = []
    current_words = 0

    for sentence in sentences:
        words = len(sentence.split())
        if current_words + words > target_words and current:
            paragraphs.append(" ".join(current))
            current = [sentence]
            current_words = words
        else:
            current.append(sentence)
            current_words += words

    if current:
        paragraphs.append(" ".join(current))

    return paragraphs
