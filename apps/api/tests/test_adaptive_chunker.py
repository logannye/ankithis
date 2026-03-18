from ankithis_api.services.chunker import chunk_section, get_chunk_params


def test_get_chunk_params_lecture_slides():
    params = get_chunk_params("lecture_slides")
    assert params["min_words"] < 800
    assert params["max_words"] < 1600


def test_get_chunk_params_research_paper():
    params = get_chunk_params("research_paper")
    assert params["min_words"] >= 600
    assert params["max_words"] >= 1600


def test_get_chunk_params_personal_notes():
    params = get_chunk_params("personal_notes")
    assert params["min_words"] <= 400
    assert params["max_words"] <= 800


def test_get_chunk_params_default():
    params = get_chunk_params("general_article")
    assert params["min_words"] == 800
    assert params["max_words"] == 1600


def test_get_chunk_params_unknown_type():
    params = get_chunk_params("unknown_type_xyz")
    assert params["min_words"] == 800
    assert params["max_words"] == 1600


def test_chunk_section_with_custom_params():
    """Verify chunk_section respects min_words/max_words overrides."""
    paragraphs = ["Word " * 50 for _ in range(10)]  # 10 paragraphs of 50 words each = 500 total
    # With default params (min=800), everything merges into one chunk
    default_chunks = chunk_section(paragraphs)
    # With small params (min=30, max=100), should produce multiple chunks
    small_chunks = chunk_section(paragraphs, min_words=30, max_words=100)
    assert len(small_chunks) > len(default_chunks)
