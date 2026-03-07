from ankithis_api.services.chunker import chunk_section


def test_small_text_single_chunk():
    """Text under MIN_CHUNK_WORDS stays as one chunk."""
    paragraphs = ["This is a short paragraph."] * 10
    chunks = chunk_section(paragraphs)
    assert len(chunks) == 1
    assert chunks[0].position == 0


def test_large_text_splits():
    """Text exceeding MAX_CHUNK_WORDS gets split into multiple chunks."""
    # Each paragraph ~100 words → 20 paragraphs = ~2000 words → should split
    paragraph = " ".join(["word"] * 100)
    paragraphs = [paragraph] * 20
    chunks = chunk_section(paragraphs)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.word_count > 0


def test_chunk_word_counts():
    """Each chunk reports accurate word counts."""
    paragraph = " ".join(["test"] * 500)
    paragraphs = [paragraph, paragraph, paragraph]  # 1500 words total
    chunks = chunk_section(paragraphs)
    total = sum(c.word_count for c in chunks)
    assert total == 1500


def test_empty_paragraphs():
    """Empty input returns no chunks."""
    chunks = chunk_section([])
    assert chunks == []


def test_positions_sequential():
    """Chunk positions are sequential starting from start_position."""
    paragraph = " ".join(["word"] * 900)
    paragraphs = [paragraph, paragraph, paragraph]
    chunks = chunk_section(paragraphs, start_position=5)
    positions = [c.position for c in chunks]
    for i in range(len(positions) - 1):
        assert positions[i + 1] > positions[i]
    assert positions[0] == 5


def test_single_huge_paragraph():
    """A paragraph exceeding MAX_CHUNK_WORDS gets its own chunk."""
    huge = " ".join(["word"] * 2000)
    chunks = chunk_section([huge])
    assert len(chunks) == 1
    assert chunks[0].word_count == 2000
