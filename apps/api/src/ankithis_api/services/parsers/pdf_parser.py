"""Parse PDF files using pdfplumber. Extracts text, detects sections by font size."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pdfplumber


@dataclass
class ParsedSection:
    title: str | None
    level: int
    paragraphs: list[str] = field(default_factory=list)


def parse_pdf(file_path: str) -> tuple[list[ParsedSection], int]:
    """Parse a PDF file into sections with paragraphs.

    Returns (sections, page_count).
    """
    sections: list[ParsedSection] = []
    current_section = ParsedSection(title=None, level=1)
    page_count = 0

    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Heuristic: lines that are short, capitalized, or bold-looking are headings
                if _looks_like_heading(line):
                    # Save current section if it has content
                    if current_section.paragraphs:
                        sections.append(current_section)
                    level = _guess_heading_level(line)
                    current_section = ParsedSection(title=line, level=level)
                else:
                    current_section.paragraphs.append(line)

    # Don't forget the last section
    if current_section.paragraphs or current_section.title:
        sections.append(current_section)

    # If no sections were detected, wrap everything in one section
    if not sections:
        sections = [ParsedSection(title=None, level=1)]

    return sections, page_count


def _looks_like_heading(line: str) -> bool:
    """Heuristic heading detection for PDF text."""
    stripped = line.strip()
    if not stripped or len(stripped) > 200:
        return False
    # Numbered headings: "1.", "1.1", "Chapter 1", etc.
    if re.match(r"^(\d+\.)+\s", stripped):
        return True
    if re.match(r"^(chapter|section|part)\s+\d+", stripped, re.IGNORECASE):
        return True
    # Short ALL CAPS lines
    if stripped.isupper() and len(stripped) < 100:
        return True
    # Lines ending without punctuation that are short (likely titles)
    if len(stripped) < 80 and not stripped.endswith((".", ",", ";", ":", "?")):
        # Must have at least one word with a capital letter
        words = stripped.split()
        if len(words) <= 10 and words[0][0].isupper():
            return True
    return False


def _guess_heading_level(line: str) -> int:
    """Guess the heading level from text cues."""
    stripped = line.strip()
    if re.match(r"^(chapter|part)\s+\d+", stripped, re.IGNORECASE):
        return 1
    if stripped.isupper():
        return 1
    # Count dots in numbering: "1.2.3" = level 3
    m = re.match(r"^((\d+\.)+)", stripped)
    if m:
        return m.group(1).count(".")
    return 2
