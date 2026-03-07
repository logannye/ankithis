"""Tests for Stage E: Critique."""

from unittest.mock import patch


@patch("ankithis_api.services.stages.critique.structured_call")
def test_critique_returns_verdicts(mock_call):
    mock_call.return_value = {
        "reviews": [
            {"card_index": 0, "verdict": "pass", "front": "", "back": "", "reason": ""},
            {"card_index": 1, "verdict": "rewrite", "front": "Fixed front", "back": "Fixed back", "reason": "bad wording"},
            {"card_index": 2, "verdict": "suppress", "front": "", "back": "", "reason": "trivial"},
        ]
    }

    from ankithis_api.services.stages.critique import critique_cards

    cards = [
        {"front": "Good card", "back": "Answer", "card_type": "basic"},
        {"front": "Bad wording", "back": "Answer", "card_type": "basic"},
        {"front": "Trivial card", "back": "Obvious", "card_type": "basic"},
    ]
    reviews = critique_cards(cards, source_text="Some source text")
    assert len(reviews) == 3
    assert reviews[0]["verdict"] == "pass"
    assert reviews[1]["verdict"] == "rewrite"
    assert reviews[2]["verdict"] == "suppress"


@patch("ankithis_api.services.stages.critique.structured_call")
def test_critique_empty_input(mock_call):
    from ankithis_api.services.stages.critique import critique_cards

    result = critique_cards([], source_text="")
    assert result == []
    mock_call.assert_not_called()


def test_apply_critique_pass():
    from ankithis_api.services.stages.critique import apply_critique

    cards = [{"front": "Q?", "back": "A", "card_type": "basic"}]
    reviews = [{"card_index": 0, "verdict": "pass", "front": "", "back": ""}]
    result = apply_critique(cards, reviews)
    assert result[0]["critique_verdict"] == "pass"
    assert not result[0].get("suppressed")


def test_apply_critique_rewrite():
    from ankithis_api.services.stages.critique import apply_critique

    cards = [{"front": "Bad Q?", "back": "Bad A", "card_type": "basic"}]
    reviews = [{"card_index": 0, "verdict": "rewrite", "front": "Good Q?", "back": "Good A"}]
    result = apply_critique(cards, reviews)
    assert result[0]["front"] == "Good Q?"
    assert result[0]["back"] == "Good A"
    assert result[0]["critique_verdict"] == "rewrite"


def test_apply_critique_suppress():
    from ankithis_api.services.stages.critique import apply_critique

    cards = [{"front": "Trivial", "back": "Obvious", "card_type": "basic"}]
    reviews = [{"card_index": 0, "verdict": "suppress", "front": "", "back": ""}]
    result = apply_critique(cards, reviews)
    assert result[0]["suppressed"] is True
    assert result[0]["critique_verdict"] == "suppress"
