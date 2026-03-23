from ankithis_api.services.qc import _check_card


def test_trivia_detection():
    card = {"front": "What year was penicillin discovered?", "back": "1928", "card_type": "basic"}
    reason = _check_card(card)
    assert reason is not None
    assert "trivia" in reason


def test_verbatim_detection():
    source = (
        "The mitochondria is the powerhouse of the cell"
        " and produces ATP through oxidative phosphorylation."
    )
    card = {
        "front": "What is the mitochondria?",
        "back": (
            "The mitochondria is the powerhouse of the cell"
            " and produces ATP through oxidative phosphorylation."
        ),
        "card_type": "basic",
    }
    reason = _check_card(card, source_text=source)
    assert reason is not None
    assert "verbatim" in reason


def test_ambiguous_cloze_detection():
    card = {
        "front": "The {{c1::process}} is important.",
        "back": "",
        "card_type": "cloze",
    }
    reason = _check_card(card)
    assert reason is not None
    assert "ambiguous" in reason


def test_compound_question_detection():
    card = {
        "front": "What is mitosis and what are its four stages?",
        "back": "Cell division; prophase, metaphase, anaphase, telophase",
        "card_type": "basic",
    }
    reason = _check_card(card)
    assert reason is not None
    assert "compound" in reason


def test_missing_context_detection():
    card = {"front": "What is it?", "back": "A protein.", "card_type": "basic"}
    reason = _check_card(card)
    assert reason is not None


def test_good_card_passes():
    card = {
        "front": (
            "In enzyme kinetics, what does a low Km value indicate about substrate affinity?"
        ),
        "back": (
            "High affinity — the enzyme reaches half-maximal"
            " velocity at low substrate concentration."
        ),
        "card_type": "basic",
    }
    reason = _check_card(card)
    assert reason is None


def test_good_cloze_passes():
    card = {
        "front": "In glycolysis, {{c1::pyruvate}} is the final product of glucose breakdown.",
        "back": "",
        "card_type": "cloze",
    }
    reason = _check_card(card)
    assert reason is None


def test_verbatim_not_triggered_without_source():
    card = {
        "front": "What is X?",
        "back": "X is a long explanation that would overlap with source text heavily.",
        "card_type": "basic",
    }
    reason = _check_card(card)
    # Should not trigger verbatim without source_text
    assert reason is None or "verbatim" not in (reason or "")
