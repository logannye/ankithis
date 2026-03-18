"""Stage C: Card Planning — decide how many cards, types, and directions."""

_BASE_SYSTEM = """\
You are an expert Anki flashcard designer. Given a set of merged concepts \
and a target deck size, plan the flashcards to create.

Card types:
- cloze: A sentence with {{{{c1::blanked term}}}} — best for definitions, \
facts, fill-in-the-blank
- basic: A question on front, answer on back — best for explanations, \
comparisons, reasoning

Rules:
- Each concept should get 1-3 cards depending on complexity
- High-importance concepts (8-10) get more cards
- The "direction" field describes exactly what the card tests
- Prefer cloze for definitions and specific facts
- Prefer basic for "why" questions, comparisons, and processes
- Card style preference: {card_style}
- Target total cards: {target_cards}
"""

DENSITY_MODIFIERS: dict[str, float] = {
    "sparse": 1.5,
    "moderate": 1.0,
    "dense": 0.8,
    "very_dense": 0.6,
}

USER_TEMPLATE = """\
Plan flashcards for these concepts. Target approximately {target_cards} cards total.
Card style preference: {card_style}
Study goal: {study_goal}

Concepts:
{concepts_json}

Plan the cards, specifying type and direction for each.
"""


# Backward compatibility
SYSTEM = _BASE_SYSTEM
