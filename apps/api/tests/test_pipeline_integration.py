"""Integration tests: Stage 0 classification wiring into the pipeline."""

from ankithis_api.services.stages.classification import classify_document, DEFAULT_PROFILE
from ankithis_api.services.section_annotator import annotate_section
from ankithis_api.services.chunker import get_chunk_params


def test_profile_flows_to_chunk_params():
    """get_chunk_params returns valid min/max for every content type."""
    for ct in ["lecture_slides", "research_paper", "personal_notes",
               "textbook_chapter", "technical_docs", "general_article",
               "video_lecture", "video_tutorial", "video_demo"]:
        profile = dict(DEFAULT_PROFILE, content_type=ct)
        params = get_chunk_params(profile["content_type"])
        assert "min_words" in params
        assert "max_words" in params
        assert params["min_words"] < params["max_words"], (
            f"{ct}: min_words={params['min_words']} >= max_words={params['max_words']}"
        )


def test_section_annotation_returns_valid_function():
    """annotate_section returns one of the known pedagogical functions."""
    valid = {
        "definitions", "theory", "methodology", "examples",
        "data_results", "summary", "code", "enumeration", "unknown",
    }
    result = annotate_section("Methods", "The protocol involves...")
    assert result in valid

    result2 = annotate_section("Results", "Figure 1 shows the data")
    assert result2 in valid

    result3 = annotate_section(None, "Some random paragraph text here")
    assert result3 in valid


def test_default_profile_compatible_with_all_stages():
    """Verify DEFAULT_PROFILE has all fields needed by downstream stages."""
    profile = DEFAULT_PROFILE
    assert "content_type" in profile
    assert "difficulty" in profile
    assert "information_density" in profile
    assert "special_considerations" in profile
    assert isinstance(profile["special_considerations"], list)
    assert "domain" in profile
    assert "structure_quality" in profile
    assert "primary_knowledge_type" in profile
    assert "recommended_cloze_ratio" in profile
    assert "recommended_qa_ratio" in profile


def test_classifying_job_status_exists():
    """JobStatus enum includes CLASSIFYING."""
    from ankithis_api.models.enums import JobStatus
    assert hasattr(JobStatus, "CLASSIFYING")
    assert JobStatus.CLASSIFYING.value == "classifying"


def test_content_profile_model_importable():
    """ContentProfile model can be imported and instantiated."""
    from ankithis_api.models.content_profile import ContentProfile
    # Just verify the class exists and has expected columns
    assert hasattr(ContentProfile, "document_id")
    assert hasattr(ContentProfile, "content_type")
    assert hasattr(ContentProfile, "difficulty")
    assert hasattr(ContentProfile, "special_considerations")
