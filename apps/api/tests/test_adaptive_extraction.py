"""Tests for profile-aware Stage A prompt builders."""

from ankithis_api.llm.prompts.stage_a import build_system_prompt, build_user_prompt


def test_system_prompt_adapts_to_research_paper():
    prompt = build_system_prompt(content_type="research_paper", difficulty="advanced")
    assert "claims" in prompt.lower() or "findings" in prompt.lower()
    assert "evidence" in prompt.lower()


def test_system_prompt_adapts_to_lecture_slides():
    prompt = build_system_prompt(content_type="lecture_slides", difficulty="introductory")
    assert "bullet" in prompt.lower() or "slide" in prompt.lower()
    assert "beginner" in prompt.lower() or "simpler" in prompt.lower()


def test_system_prompt_adapts_to_pedagogical_function():
    prompt = build_system_prompt(pedagogical_function="definitions")
    assert "term" in prompt.lower() or "meaning" in prompt.lower()


def test_system_prompt_default():
    prompt = build_system_prompt()
    assert "concept" in prompt.lower()


def test_user_prompt_includes_visual_context():
    prompt = build_user_prompt(
        chunk_text="Some text",
        study_goal="Learn biology",
        visual_context="Diagram shows cell membrane structure",
    )
    assert "cell membrane" in prompt
    assert "visual" in prompt.lower()


def test_user_prompt_no_visual_context():
    prompt = build_user_prompt(chunk_text="Some text", study_goal="Learn bio")
    assert "visual" not in prompt.lower()


def test_backward_compat_constants():
    from ankithis_api.llm.prompts.stage_a import SYSTEM, USER_TEMPLATE

    assert "concept" in SYSTEM.lower()
    assert "{chunk_text}" in USER_TEMPLATE
    assert "{study_goal}" in USER_TEMPLATE
