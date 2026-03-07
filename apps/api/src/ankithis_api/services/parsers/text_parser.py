"""Parse TXT and Markdown files. Uses # headings for Markdown, blank-line heuristics for TXT."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ParsedSection:
    title: str | None
    level: int
    paragraphs: list[str] = field(default_factory=list)


def parse_text(file_path: str) -> list[ParsedSection]:
    """Parse a plain text file into sections using blank-line heuristics."""
    with open(file_path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    return _split_into_sections(content, is_markdown=False)


def parse_markdown(file_path: str) -> list[ParsedSection]:
    """Parse a Markdown file into sections using # heading syntax."""
    with open(file_path, encoding="utf-8", errors="replace") as f:
        content = f.read()
    return _split_into_sections(content, is_markdown=True)


def _split_into_sections(content: str, is_markdown: bool) -> list[ParsedSection]:
    lines = content.split("\n")
    sections: list[ParsedSection] = []
    current_section = ParsedSection(title=None, level=1)

    for line in lines:
        stripped = line.strip()

        if is_markdown and stripped.startswith("#"):
            # Markdown heading
            m = re.match(r"^(#+)\s+(.*)", stripped)
            if m:
                if current_section.paragraphs or current_section.title:
                    sections.append(current_section)
                level = len(m.group(1))
                title = m.group(2).strip()
                current_section = ParsedSection(title=title, level=level)
                continue

        if not is_markdown and _looks_like_text_heading(stripped, lines):
            if current_section.paragraphs or current_section.title:
                sections.append(current_section)
            current_section = ParsedSection(title=stripped, level=2)
            continue

        if stripped:
            current_section.paragraphs.append(stripped)

    if current_section.paragraphs or current_section.title:
        sections.append(current_section)

    if not sections:
        sections = [ParsedSection(title=None, level=1)]

    return sections


def _looks_like_text_heading(line: str, all_lines: list[str]) -> bool:
    """Heuristic for headings in plain text."""
    if not line or len(line) > 100:
        return False
    # All caps short lines
    if line.isupper() and len(line) < 80:
        return True
    # Numbered headings
    if re.match(r"^\d+\.\s+\w", line):
        return True
    return False
