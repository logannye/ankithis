"""Heuristic section-level pedagogical function annotation."""

from __future__ import annotations

import re

# Heading patterns -> function
_HEADING_SIGNALS: list[tuple[str, re.Pattern]] = [
    ("definitions", re.compile(r"defini|glossar|terminolog|vocabulary", re.I)),
    (
        "methodology",
        re.compile(
            r"method|protocol|procedure|materials and|experimental setup",
            re.I,
        ),
    ),
    ("data_results", re.compile(r"result|finding|data|figure|table\b|observation", re.I)),
    ("summary", re.compile(r"summar|conclusion|takeaway|key point|recap|review", re.I)),
    ("examples", re.compile(r"example|case stud|scenario|illustration|exercise", re.I)),
    ("theory", re.compile(r"theor|framework|model|mechanism|principle|concept", re.I)),
]

# First-paragraph patterns -> function
_BODY_SIGNALS: list[tuple[str, re.Pattern]] = [
    ("definitions", re.compile(r"is defined as|refers to|definition of|meaning of", re.I)),
    ("methodology", re.compile(r"step[s ]?\d|protocol|procedure|the following steps", re.I)),
    (
        "data_results",
        re.compile(
            r"figure \d|table \d|p\s*[<>]\s*0\.\d|statistically significant",
            re.I,
        ),
    ),
    ("summary", re.compile(r"in summary|to summarize|key takeaway|in conclusion", re.I)),
    ("examples", re.compile(r"consider the following|for example|for instance|suppose that", re.I)),
    ("code", re.compile(r"```|def \w+\(|class \w+|function \w+|import \w+", re.I)),
    ("enumeration", re.compile(r"^[\s]*[-\u2022*]\s+\w+.*\n[\s]*[-\u2022*]\s+\w+", re.M)),
    ("theory", re.compile(r"mechanism|principle|model|the relationship between", re.I)),
]


def annotate_section(title: str | None, first_paragraph: str) -> str:
    """Return pedagogical function label for a section.

    Uses heading text first, then falls back to first-paragraph content signals.
    Returns 'unknown' if confidence is low.
    """
    # Check heading signals
    if title:
        for func, pattern in _HEADING_SIGNALS:
            if pattern.search(title):
                return func

    # Check body signals
    text = first_paragraph[:500]
    for func, pattern in _BODY_SIGNALS:
        if pattern.search(text):
            return func

    return "unknown"
