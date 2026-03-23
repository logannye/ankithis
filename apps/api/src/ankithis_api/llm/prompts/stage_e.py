"""Stage E: Critique — evaluate card quality and rewrite if needed."""

_BASE_SYSTEM = """\
You are an expert Anki flashcard quality reviewer. Evaluate each card against \
this rubric and give a verdict.

Quality rubric:
- The card tests exactly ONE piece of knowledge
- Cloze blanks are 1-4 words (the specific term, not filler words)
- The surrounding context is sufficient to recall the blank
- Basic card questions are specific and unambiguous
- Answers are concise and self-contained
- No encoding issues, broken formatting, or nonsensical text
- The card is factually consistent with the source material

Verdicts:
- "pass": Card meets all quality criteria
- "rewrite": Card has fixable issues — provide a corrected version
- "suppress": Card is fundamentally flawed, redundant with its own text, \
or tests trivial/obvious information — remove it

For "rewrite" verdicts, provide corrected front and back text.
For "pass" and "suppress", front and back can be empty strings.
"""

_QUALITY_BAR: dict[str, str] = {
    "research_paper": "Be STRICT — suppress any card that oversimplifies a finding or omits important caveats. Scientific accuracy is non-negotiable.",
    "lecture_slides": "Be MODERATE — accept cards that capture the gist even if slightly imprecise. Slides are already simplified.",
    "personal_notes": "Be LENIENT — respect the user's own framing. Only suppress factually wrong or truly ambiguous cards.",
    "technical_docs": "Be STRICT on accuracy — a wrong API parameter or behavior is worse than no card at all.",
    "textbook_chapter": "Be MODERATE — balance accuracy with accessibility.",
    "general_article": "Be MODERATE — standard quality bar.",
}

_ANTI_PATTERN_INSTRUCTIONS = """\
Also check for these anti-patterns:
- TRIVIA: Cards asking "what year", "who discovered" without testing understanding -> suppress
- VERBATIM: Card back is a near-copy of the source text -> rewrite in the card's own words
- AMBIGUOUS CLOZE: The blank could be filled by multiple correct answers -> rewrite with more context
- COMPOUND: Card tests two independent questions joined by "and" -> rewrite as separate concepts
"""

_BLOOMS_CRITIQUE_INSTRUCTION = """\
Bloom's alignment check:
- If a card's plan specifies bloom_level, verify the generated question matches that level.
- A card targeting 'analyze' that merely asks 'What is the definition of X?' should get \
verdict 'rewrite' with guidance to ask a comparison or differentiation question instead.
- A card targeting 'apply' that only tests recall should be rewritten to present a scenario.
- A card targeting 'evaluate' should require the learner to judge, not just describe.
"""

USER_TEMPLATE = """\
Review these flashcards for quality. Source material is provided for \
fact-checking.

Source text (excerpt):
{source_text}

Cards to review:
{cards_json}

For each card, provide a verdict (pass/rewrite/suppress) and corrected \
text if rewriting.
"""


def build_system_prompt(
    content_type: str | None = None,
    has_bloom_levels: bool = False,
) -> str:
    """Build an adapted system prompt for card critique.

    Parameters
    ----------
    content_type:
        Document content type — selects the quality bar.
    has_bloom_levels:
        When ``True``, the Bloom's alignment check is appended so the
        critique verifies cognitive-level consistency.
    """
    parts = [_BASE_SYSTEM, _ANTI_PATTERN_INSTRUCTIONS]
    if content_type and content_type in _QUALITY_BAR:
        parts.append(f"\nQuality threshold: {_QUALITY_BAR[content_type]}")
    if has_bloom_levels:
        parts.append(_BLOOMS_CRITIQUE_INSTRUCTION)
    return "\n".join(parts)


# Backward compatibility
SYSTEM = _BASE_SYSTEM
