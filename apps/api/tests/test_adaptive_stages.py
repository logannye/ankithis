"""Tests for profile-aware prompt builders in stages B-E."""

from ankithis_api.llm.prompts.stage_b import build_system_prompt as build_b
from ankithis_api.llm.prompts.stage_c import DENSITY_MODIFIERS
from ankithis_api.llm.prompts.stage_d import build_system_prompt as build_d
from ankithis_api.llm.prompts.stage_e import build_system_prompt as build_e


def test_stage_b_adapts_to_lecture_slides():
    prompt = build_b(content_type="lecture_slides")
    assert "aggressive" in prompt.lower()


def test_stage_b_adapts_to_research_paper():
    prompt = build_b(content_type="research_paper")
    assert "lightly" in prompt.lower() or "light" in prompt.lower()


def test_stage_b_default():
    prompt = build_b()
    assert "merge" in prompt.lower()


def test_stage_d_includes_pedagogical_principles():
    prompt = build_d()
    assert "atomic" in prompt.lower()
    assert "understanding" in prompt.lower()


def test_stage_d_adapts_to_difficulty():
    prompt = build_d(difficulty="introductory")
    assert "simple language" in prompt.lower()


def test_stage_d_includes_special_considerations():
    prompt = build_d(special_considerations=["heavy_notation", "code_examples"])
    assert "latex" in prompt.lower() or "notation" in prompt.lower()
    assert "code" in prompt.lower()


def test_stage_e_adapts_to_research_paper():
    prompt = build_e(content_type="research_paper")
    assert "strict" in prompt.lower()


def test_stage_e_adapts_to_personal_notes():
    prompt = build_e(content_type="personal_notes")
    assert "lenient" in prompt.lower()


def test_stage_e_includes_anti_patterns():
    prompt = build_e()
    assert "trivia" in prompt.lower()
    assert "verbatim" in prompt.lower()


def test_density_modifiers_exist():
    assert DENSITY_MODIFIERS["sparse"] > 1.0
    assert DENSITY_MODIFIERS["very_dense"] < 1.0
    assert DENSITY_MODIFIERS["moderate"] == 1.0
