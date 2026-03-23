"""Stage A: Concept Extraction — extract key testable concepts from text chunks."""

_BASE_SYSTEM = """\
You are an expert educator and knowledge analyst. Your job is to extract \
the key concepts from educational text that would be valuable for a student \
to learn via flashcards.

Rules:
- Extract 5-15 concepts per chunk depending on density
- Each concept should be a distinct, testable piece of knowledge
- Prefer specific facts, definitions, relationships, and processes over vague themes
- Rate importance 1-10: definitions and core mechanisms get 8-10, supporting details get 4-6
- Include a short source quote from the text that anchors each concept
- If a concept requires understanding another concept first, list those prerequisites by name
- Do NOT extract meta-commentary, table of contents items, or bibliographic references
"""

_BASE_USER_TEMPLATE = """\
Extract the key educational concepts from this text chunk. The student's \
study goal is: {study_goal}

---
{chunk_text}
---

Extract all concepts worth making flashcards about.
"""

# Content-type-specific extraction guidance
_CONTENT_TYPE_GUIDANCE: dict[str, str] = {
    "lecture_slides": (
        "This is from lecture slides. Bullets are shorthand — infer the full idea "
        "behind each bullet point. Look for relationships between points. "
        "Each slide assertion is a potential concept."
    ),
    "research_paper": (
        "This is from a research paper. Extract claims paired with their evidence. "
        "Focus on findings, methodology rationale, and stated limitations. "
        "Treat 'X causes Y (p < 0.01)' as one concept, not two."
    ),
    "textbook_chapter": (
        "This is from a textbook. Separate definitions (what), theory (why), "
        "and procedures (how). Extract worked-example logic as distinct concepts."
    ),
    "personal_notes": (
        "This is from personal notes — already condensed. Treat each note as a "
        "near-concept. Focus on filling gaps: what prerequisite knowledge does "
        "this note assume?"
    ),
    "technical_docs": (
        "This is technical documentation. Extract function behaviors, parameter "
        "effects, gotchas, and 'when to use X vs Y' decision points."
    ),
    "general_article": (
        "This is a general article. Extract the argument structure: thesis, "
        "supporting claims, evidence, and counterpoints."
    ),
    "video_lecture": (
        "This is from a video lecture transcript. The speaker may repeat points "
        "for emphasis — identify the core idea, not each repetition."
    ),
    "video_tutorial": (
        "This is from a tutorial video. Extract each step, its purpose, and "
        "common mistakes the instructor warns about."
    ),
    "video_demo": (
        "This is from a demonstration video. Extract what was shown, the "
        "technique used, and what would happen if done differently."
    ),
}

_DIFFICULTY_GUIDANCE: dict[str, str] = {
    "introductory": (
        "The audience is beginners. Extract more concepts, use simpler phrasing. "
        "Definitions are critical — vocabulary IS the learning at this level."
    ),
    "intermediate": (
        "The audience has foundational knowledge. Balance definitions with "
        "relationships. Extract 'how X relates to Y' concepts."
    ),
    "advanced": (
        "The audience is domain-fluent. Extract fewer but deeper concepts: "
        "nuances, exceptions, edge cases. Skip basics."
    ),
    "expert": (
        "The audience is expert-level. Extract only novel findings, "
        "methodological innovations, and points of disagreement in the field."
    ),
}

_KNOWLEDGE_TYPE_GUIDANCE: dict[str, str] = {
    "factual": (
        "This content is primarily factual. Prioritize definitions, data points, "
        "names, dates, and precise terminology. Each fact is a potential flashcard."
    ),
    "conceptual": (
        "This content is primarily conceptual. Prioritize relationships between ideas, "
        "mechanisms, cause-and-effect chains, and 'why' explanations."
    ),
    "procedural": (
        "This content is primarily procedural. Prioritize steps, decision points, "
        "conditions, and 'what happens if you skip step X' consequences."
    ),
    "mixed": (
        "This content mixes factual, conceptual, and procedural knowledge. "
        "Extract a balanced mix of facts, relationships, and procedures."
    ),
}

_SECTION_FUNCTION_GUIDANCE: dict[str, str] = {
    "definitions": "Focus on extracting each term with its precise meaning and one distinguishing example.",
    "theory": "Focus on mechanisms, causal relationships, and the 'why' behind phenomena.",
    "methodology": "Focus on procedural steps, rationale for key decisions, and common failure modes.",
    "examples": "Focus on the principle the example illustrates and what makes this case instructive.",
    "data_results": "Focus on what the data shows, its significance, and how to interpret key figures.",
    "summary": "This is a summary section — extract sparingly. Only capture ideas not covered earlier.",
    "code": "Focus on what the code does, key syntax patterns, and behavioral edge cases.",
    "enumeration": "Each list item may be a separate concept. Extract the distinguishing property of each.",
}


def build_system_prompt(
    content_type: str | None = None,
    difficulty: str | None = None,
    pedagogical_function: str | None = None,
    knowledge_type: str | None = None,
) -> str:
    """Build an adapted system prompt for concept extraction."""
    parts = [_BASE_SYSTEM]

    if content_type and content_type in _CONTENT_TYPE_GUIDANCE:
        parts.append(f"\nContent context: {_CONTENT_TYPE_GUIDANCE[content_type]}")

    if difficulty and difficulty in _DIFFICULTY_GUIDANCE:
        parts.append(f"\nAudience level: {_DIFFICULTY_GUIDANCE[difficulty]}")

    if pedagogical_function and pedagogical_function in _SECTION_FUNCTION_GUIDANCE:
        parts.append(f"\nSection focus: {_SECTION_FUNCTION_GUIDANCE[pedagogical_function]}")

    if knowledge_type and knowledge_type in _KNOWLEDGE_TYPE_GUIDANCE:
        parts.append(f"\nKnowledge type: {_KNOWLEDGE_TYPE_GUIDANCE[knowledge_type]}")

    return "\n".join(parts)


def build_user_prompt(
    chunk_text: str,
    study_goal: str = "Master the key concepts in this material",
    visual_context: str | None = None,
) -> str:
    """Build an adapted user prompt, optionally including visual context."""
    base = _BASE_USER_TEMPLATE.format(study_goal=study_goal, chunk_text=chunk_text)

    if visual_context:
        base += f"\n\nVisual context (from video/diagrams):\n{visual_context}"

    return base


# Backward compatibility
SYSTEM = _BASE_SYSTEM
USER_TEMPLATE = _BASE_USER_TEMPLATE
