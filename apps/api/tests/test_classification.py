from ankithis_api.services.stages.classification import (
    _build_sample, _safe_classify, DEFAULT_PROFILE,
)
from ankithis_api.services.parser import ParsedSection

def test_build_sample_extracts_headings_and_text():
    sections = [
        ParsedSection(title="Introduction", level=1, paragraphs=["First para. " * 200]),
        ParsedSection(title="Methods", level=1, paragraphs=["Method text here."]),
    ]
    headings, opening, closing = _build_sample(sections)
    assert "Introduction" in headings
    assert "Methods" in headings
    assert "First para." in opening
    assert len(opening) <= 12000

def test_safe_classify_returns_default_on_failure():
    profile = _safe_classify("", "", "")
    assert profile["content_type"] == DEFAULT_PROFILE["content_type"]
    assert profile["difficulty"] == DEFAULT_PROFILE["difficulty"]

def test_default_profile_has_all_fields():
    assert "content_type" in DEFAULT_PROFILE
    assert "domain" in DEFAULT_PROFILE
    assert "difficulty" in DEFAULT_PROFILE
    assert "information_density" in DEFAULT_PROFILE
    assert "recommended_cloze_ratio" in DEFAULT_PROFILE
    assert "special_considerations" in DEFAULT_PROFILE

def test_build_sample_handles_empty_sections():
    sections = []
    headings, opening, closing = _build_sample(sections)
    assert headings == ""
    assert opening == ""
    assert closing == ""

def test_build_sample_handles_no_titles():
    sections = [ParsedSection(title=None, level=1, paragraphs=["Some text here."])]
    headings, opening, closing = _build_sample(sections)
    assert headings == ""
    assert "Some text" in opening
