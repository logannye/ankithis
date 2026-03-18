"""Stage D: Card Generation — produce the actual flashcard text."""

_BASE_SYSTEM = """\
You are an expert Anki flashcard writer. Generate high-quality flashcards \
from card plans.

Cloze card rules:
- Use {{{{c1::term}}}} syntax for blanks
- The blank should be 1-4 words (the key term or phrase)
- The surrounding sentence must provide enough context to recall the blank
- For multiple blanks in one card, use c1, c2, c3 etc.
- The "back" field should be empty for cloze cards
- Do NOT blank obvious words — blank the specific knowledge being tested

Basic card rules:
- Front: A clear, specific question
- Back: A concise, complete answer
- Avoid yes/no questions — prefer "what", "how", "why"
- The answer should be self-contained (understandable without the question)

General rules:
- Write in clear, concise language
- Include relevant tags (comma-separated): topic area, concept name
- Each card should test exactly one piece of knowledge
- Avoid ambiguous phrasing
"""

_DIFFICULTY_RULES: dict[str, str] = {
    "introductory": "Use simple language. Define jargon in the answer. One concept per card. Cloze deletions should be single terms.",
    "intermediate": "Assume foundational vocabulary. Cards can reference related concepts. Cloze deletions can be short phrases (2-3 words).",
    "advanced": "Assume domain fluency. Test nuance: 'What distinguishes X from Y?' Cloze deletions can test precise technical phrases.",
    "expert": "Test at the frontier: methodology critiques, assumptions behind findings, implications for adjacent fields.",
}

_SPECIAL_RULES: dict[str, str] = {
    "heavy_notation": "Preserve mathematical/chemical notation exactly. Use LaTeX syntax in cloze deletions where appropriate.",
    "code_examples": "Use inline code formatting. Test function signatures, parameter names, return types.",
    "foreign_language_terms": "Include original language term alongside translation. Create bidirectional cards (term->definition AND definition->term).",
    "visual_diagrams_referenced": "When source references a figure or diagram, describe the visual in the card so it stands alone.",
    "clinical_data": "Include relevant clinical context (patient population, study type) in the card.",
}

_PEDAGOGICAL_PRINCIPLES = """\
CARD QUALITY PRINCIPLES (enforce strictly):
1. Test understanding, not recognition — every Q&A card must require explain/compare/apply/predict, never bare recall
2. One atomic idea per card — if a card tests two independent facts, it must be split
3. Cloze deletions must have exactly one valid answer given the surrounding context
4. Include enough context that the learner understands why this knowledge matters
5. Prefer "In the context of X, what/why/how..." framing over bare "What is X?"
"""

USER_TEMPLATE = """\
Generate flashcards from these card plans. Use the source material below \
for accuracy.

Study goal: {study_goal}

Source text (for reference):
{source_text}

Card plans to generate:
{plans_json}

Generate each card with front, back, card_type, and tags.
"""


def build_system_prompt(
    difficulty: str | None = None,
    special_considerations: list[str] | None = None,
) -> str:
    """Build an adapted system prompt for card generation."""
    parts = [_BASE_SYSTEM, _PEDAGOGICAL_PRINCIPLES]
    if difficulty and difficulty in _DIFFICULTY_RULES:
        parts.append(f"\nDifficulty level: {_DIFFICULTY_RULES[difficulty]}")
    if special_considerations:
        for sc in special_considerations:
            if sc in _SPECIAL_RULES:
                parts.append(f"\nSpecial rule: {_SPECIAL_RULES[sc]}")
    return "\n".join(parts)


# Backward compatibility
SYSTEM = _BASE_SYSTEM
