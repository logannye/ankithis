"""Deterministic quality control filters for generated cards."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Cloze blank content should be 1-4 words
CLOZE_MAX_BLANK_WORDS = 4
# Minimum front text length
MIN_FRONT_LENGTH = 20
# Maximum front text length (likely garbage)
MAX_FRONT_LENGTH = 2000

CLOZE_PATTERN = re.compile(r"\{\{c\d+::([^}]+)\}\}")


def run_qc(cards: list[dict]) -> list[dict]:
    """Run deterministic QC filters on cards.

    Sets suppressed=True and qc_reason on cards that fail.
    Returns the same list with modifications applied.
    """
    for card in cards:
        if card.get("suppressed"):
            continue

        reason = _check_card(card)
        if reason:
            card["suppressed"] = True
            card["qc_reason"] = reason
            logger.info(f"QC suppressed card: {reason}")

    return cards


def _check_card(card: dict) -> str | None:
    """Check a single card. Returns reason string if it fails, None if it passes."""
    front = card.get("front", "")
    back = card.get("back", "")
    card_type = card.get("card_type", "basic")

    # Check for empty/missing front
    if not front or not front.strip():
        return "empty_front"

    # Check minimum front length
    if len(front.strip()) < MIN_FRONT_LENGTH:
        return "front_too_short"

    # Check maximum front length
    if len(front.strip()) > MAX_FRONT_LENGTH:
        return "front_too_long"

    # Check for encoding issues / garbled text
    if _has_encoding_issues(front) or _has_encoding_issues(back):
        return "encoding_issues"

    # Cloze-specific checks
    if card_type == "cloze":
        blanks = CLOZE_PATTERN.findall(front)
        if not blanks:
            return "cloze_no_blanks"

        for blank_content in blanks:
            word_count = len(blank_content.strip().split())
            if word_count > CLOZE_MAX_BLANK_WORDS:
                return f"cloze_blank_too_long ({word_count} words)"

    # Basic card: back should not be empty
    if card_type == "basic" and (not back or not back.strip()):
        return "basic_empty_back"

    return None


def _has_encoding_issues(text: str) -> bool:
    """Check for common encoding issues in text."""
    if not text:
        return False

    # Replacement character
    if "\ufffd" in text:
        return True

    # Excessive control characters (excluding newlines/tabs)
    control_chars = sum(1 for c in text if ord(c) < 32 and c not in "\n\r\t")
    if control_chars > 3:
        return True

    return False
