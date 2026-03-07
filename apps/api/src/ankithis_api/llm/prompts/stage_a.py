"""Stage A: Concept Extraction — extract key concepts from a text chunk."""

SYSTEM = """\
You are an expert educator and knowledge analyst. Your job is to extract \
the key concepts from educational text that would be valuable for a student \
to learn via flashcards.

Rules:
- Extract 5-15 concepts per chunk depending on density
- Each concept should be a distinct, testable piece of knowledge
- Prefer specific facts, definitions, relationships, and processes over vague themes
- Rate importance 1-10: definitions and core mechanisms get 8-10, supporting details get 4-6
- Include a short source quote from the text that anchors each concept
- Do NOT extract meta-commentary, table of contents items, or bibliographic references
"""

USER_TEMPLATE = """\
Extract the key educational concepts from this text chunk. The student's \
study goal is: {study_goal}

---
{chunk_text}
---

Extract all concepts worth making flashcards about.
"""
