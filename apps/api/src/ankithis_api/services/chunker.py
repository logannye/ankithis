"""Section-aware text chunker. Splits sections into 800-1600 word chunks at paragraph boundaries."""

from __future__ import annotations

from dataclasses import dataclass

MIN_CHUNK_WORDS = 800
MAX_CHUNK_WORDS = 1600

CHUNK_PARAMS_BY_TYPE: dict[str, dict[str, int]] = {
    "lecture_slides": {"min_words": 30, "max_words": 400},
    "research_paper": {"min_words": 600, "max_words": 2000},
    "textbook_chapter": {"min_words": 1000, "max_words": 2000},
    "personal_notes": {"min_words": 200, "max_words": 800},
    "technical_docs": {"min_words": 400, "max_words": 1200},
    "general_article": {"min_words": 800, "max_words": 1600},
    "video_lecture": {"min_words": 600, "max_words": 1400},
    "video_tutorial": {"min_words": 400, "max_words": 1000},
    "video_demo": {"min_words": 400, "max_words": 1000},
}


def get_chunk_params(content_type: str) -> dict[str, int]:
    """Return chunking parameters for a content type."""
    return CHUNK_PARAMS_BY_TYPE.get(
        content_type,
        {"min_words": MIN_CHUNK_WORDS, "max_words": MAX_CHUNK_WORDS},
    )


@dataclass
class TextChunk:
    text: str
    word_count: int
    position: int


def chunk_section(
    paragraphs: list[str],
    start_position: int = 0,
    min_words: int | None = None,
    max_words: int | None = None,
) -> list[TextChunk]:
    """Split a list of paragraphs into word-bounded chunks.

    Tries to keep chunks between *min_words* and *max_words*,
    splitting at paragraph boundaries. If a single paragraph exceeds
    *max_words*, it gets its own chunk.

    When *min_words* / *max_words* are ``None`` the module-level
    ``MIN_CHUNK_WORDS`` / ``MAX_CHUNK_WORDS`` constants are used.
    """
    if not paragraphs:
        return []

    effective_min = min_words if min_words is not None else MIN_CHUNK_WORDS
    effective_max = max_words if max_words is not None else MAX_CHUNK_WORDS

    chunks: list[TextChunk] = []
    current_paragraphs: list[str] = []
    current_words = 0
    position = start_position

    for para in paragraphs:
        para_words = len(para.split())

        # If adding this paragraph would exceed max and we already have content,
        # flush the current chunk first
        if current_words + para_words > effective_max and current_paragraphs:
            chunks.append(
                TextChunk(
                    text="\n\n".join(current_paragraphs),
                    word_count=current_words,
                    position=position,
                )
            )
            position += 1
            current_paragraphs = []
            current_words = 0

        current_paragraphs.append(para)
        current_words += para_words

        # If we've reached a good size, flush
        if current_words >= effective_min:
            chunks.append(
                TextChunk(
                    text="\n\n".join(current_paragraphs),
                    word_count=current_words,
                    position=position,
                )
            )
            position += 1
            current_paragraphs = []
            current_words = 0

    # Remaining content
    if current_paragraphs:
        # If there's a previous chunk and the remaining is very small, merge
        if chunks and current_words < effective_min // 2:
            last = chunks[-1]
            merged_text = last.text + "\n\n" + "\n\n".join(current_paragraphs)
            chunks[-1] = TextChunk(
                text=merged_text,
                word_count=last.word_count + current_words,
                position=last.position,
            )
        else:
            chunks.append(
                TextChunk(
                    text="\n\n".join(current_paragraphs),
                    word_count=current_words,
                    position=position,
                )
            )

    return chunks
