"""Section-aware text chunker. Splits sections into 800-1600 word chunks at paragraph boundaries."""

from __future__ import annotations

from dataclasses import dataclass

MIN_CHUNK_WORDS = 800
MAX_CHUNK_WORDS = 1600


@dataclass
class TextChunk:
    text: str
    word_count: int
    position: int


def chunk_section(paragraphs: list[str], start_position: int = 0) -> list[TextChunk]:
    """Split a list of paragraphs into word-bounded chunks.

    Tries to keep chunks between MIN_CHUNK_WORDS and MAX_CHUNK_WORDS,
    splitting at paragraph boundaries. If a single paragraph exceeds
    MAX_CHUNK_WORDS, it gets its own chunk.
    """
    if not paragraphs:
        return []

    chunks: list[TextChunk] = []
    current_paragraphs: list[str] = []
    current_words = 0
    position = start_position

    for para in paragraphs:
        para_words = len(para.split())

        # If adding this paragraph would exceed max and we already have content,
        # flush the current chunk first
        if current_words + para_words > MAX_CHUNK_WORDS and current_paragraphs:
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
        if current_words >= MIN_CHUNK_WORDS:
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
        if chunks and current_words < MIN_CHUNK_WORDS // 2:
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
