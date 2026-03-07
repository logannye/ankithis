"""Tests for deterministic QC filters."""

from ankithis_api.services.qc import run_qc


def test_qc_passes_good_cloze():
    cards = [{"front": "{{c1::Mitochondria}} are the powerhouse of the cell.", "back": "", "card_type": "cloze"}]
    result = run_qc(cards)
    assert not result[0].get("suppressed")


def test_qc_passes_good_basic():
    cards = [{"front": "What organelle produces ATP in eukaryotic cells?", "back": "Mitochondria", "card_type": "basic"}]
    result = run_qc(cards)
    assert not result[0].get("suppressed")


def test_qc_suppresses_empty_front():
    cards = [{"front": "", "back": "Answer", "card_type": "basic"}]
    result = run_qc(cards)
    assert result[0]["suppressed"] is True
    assert result[0]["qc_reason"] == "empty_front"


def test_qc_suppresses_short_front():
    cards = [{"front": "What?", "back": "Answer", "card_type": "basic"}]
    result = run_qc(cards)
    assert result[0]["suppressed"] is True
    assert result[0]["qc_reason"] == "front_too_short"


def test_qc_suppresses_cloze_no_blanks():
    cards = [{"front": "This is a cloze card without any blanks at all.", "back": "", "card_type": "cloze"}]
    result = run_qc(cards)
    assert result[0]["suppressed"] is True
    assert result[0]["qc_reason"] == "cloze_no_blanks"


def test_qc_suppresses_cloze_long_blank():
    cards = [{"front": "{{c1::This is a very long blank with too many words}} in the cell.", "back": "", "card_type": "cloze"}]
    result = run_qc(cards)
    assert result[0]["suppressed"] is True
    assert "cloze_blank_too_long" in result[0]["qc_reason"]


def test_qc_suppresses_basic_empty_back():
    cards = [{"front": "What is the function of mitochondria?", "back": "", "card_type": "basic"}]
    result = run_qc(cards)
    assert result[0]["suppressed"] is True
    assert result[0]["qc_reason"] == "basic_empty_back"


def test_qc_suppresses_encoding_issues():
    cards = [{"front": "What is the function of \ufffd in cells?", "back": "Answer", "card_type": "basic"}]
    result = run_qc(cards)
    assert result[0]["suppressed"] is True
    assert result[0]["qc_reason"] == "encoding_issues"


def test_qc_skips_already_suppressed():
    cards = [{"front": "", "back": "", "card_type": "basic", "suppressed": True}]
    result = run_qc(cards)
    # Should not add qc_reason since already suppressed
    assert "qc_reason" not in result[0]
