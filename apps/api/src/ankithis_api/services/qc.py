"""Deterministic quality control filters for generated cards."""

from __future__ import annotations

import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Cloze blank content should be 1-4 words
CLOZE_MAX_BLANK_WORDS = 4
# Minimum front text length
MIN_FRONT_LENGTH = 20
# Maximum front text length (likely garbage)
MAX_FRONT_LENGTH = 2000

CLOZE_PATTERN = re.compile(r"\{\{c\d+::([^}]+)\}\}")

# --- Anti-pattern detection patterns ---

_TRIVIA_PATTERN = re.compile(
    r"\b(what year|in what year|who discovered|who invented|where was .+ born|"
    r"when was .+ (founded|established|created|born|discovered))\b",
    re.I,
)

_COMPOUND_PATTERN = re.compile(
    r"\b(what|how|why|where|when|which) .+ and (what|how|why|where|when|which) ",
    re.I,
)


def run_qc(
    cards: list[dict], *, source_text: str | None = None
) -> list[dict]:
    """Run deterministic QC filters on cards.

    Sets suppressed=True and qc_reason on cards that fail.
    Returns the same list with modifications applied.
    """
    for card in cards:
        if card.get("suppressed"):
            continue

        reason = _check_card(card, source_text=source_text)
        if reason:
            card["suppressed"] = True
            card["qc_reason"] = reason
            logger.info(f"QC suppressed card: {reason}")

    return cards


def _check_card(card: dict, source_text: str | None = None) -> str | None:
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

    # --- Pedagogical anti-pattern checks ---

    if _is_trivia(front):
        return "trivia_question"

    if _is_verbatim(card.get("back", ""), source_text):
        return "verbatim_copy"

    if card_type == "cloze" and _is_ambiguous_cloze(front):
        return "ambiguous_cloze"

    if _is_compound_question(front):
        return "compound_question"

    if _lacks_context(front, card_type):
        return "missing_context"

    return None


# --- Anti-pattern detection helpers ---


def _is_trivia(front: str) -> bool:
    """Detect trivia questions (dates, discoverers) without conceptual depth."""
    return bool(_TRIVIA_PATTERN.search(front))


def _is_verbatim(back: str, source_text: str | None) -> bool:
    """Detect >60% word overlap between card back and source text."""
    if not source_text or not back:
        return False
    back_words = Counter(re.findall(r"\w+", back.lower()))
    source_words = Counter(re.findall(r"\w+", source_text.lower()))
    if not back_words:
        return False
    overlap = sum((back_words & source_words).values())
    return (overlap / sum(back_words.values())) > 0.60


def _is_ambiguous_cloze(front: str) -> bool:
    """Detect cloze deletions where the blank is a common/vague word with little context."""
    matches = CLOZE_PATTERN.findall(front)
    if not matches:
        return False
    # Common words that are almost always ambiguous as blanks
    vague = {"process", "system", "method", "thing", "it", "this", "that", "way", "type", "form"}
    for term in matches:
        cleaned = term.strip().lower()
        if cleaned in vague:
            # Check if surrounding context is too short (< 3 substantive words before the blank)
            before_blank = front.split("{{")[0]
            words_before = [w for w in re.findall(r"\w+", before_blank) if len(w) > 2]
            if len(words_before) < 3:
                return True
    return False


def _is_compound_question(front: str) -> bool:
    """Detect questions that test two independent ideas joined by 'and'."""
    return bool(_COMPOUND_PATTERN.search(front))


def _lacks_context(front: str, card_type: str) -> bool:
    """Detect basic cards with fronts too short to provide context."""
    if card_type != "basic":
        return False
    words = front.split()
    return len(words) < 6


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
