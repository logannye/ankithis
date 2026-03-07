"""Tests for Stage F: Deduplication."""

from unittest.mock import patch


def test_token_overlap_identical():
    from ankithis_api.services.stages.dedup import _token_overlap

    assert _token_overlap("hello world", "hello world") == 1.0


def test_token_overlap_no_overlap():
    from ankithis_api.services.stages.dedup import _token_overlap

    assert _token_overlap("hello world", "foo bar") == 0.0


def test_token_overlap_partial():
    from ankithis_api.services.stages.dedup import _token_overlap

    score = _token_overlap("the cat sat on the mat", "the cat sat on a rug")
    assert 0.4 < score < 0.9


def test_find_duplicate_pairs():
    from ankithis_api.services.stages.dedup import find_duplicate_pairs

    cards = [
        {"front": "The mitochondria is the powerhouse of the cell and generates energy.", "back": "A"},
        {"front": "The mitochondria is the powerhouse of the cell and generates ATP energy.", "back": "B"},
        {"front": "Completely different card about photosynthesis in plants.", "back": "C"},
    ]
    pairs = find_duplicate_pairs(cards)
    assert len(pairs) >= 1
    # First two should be flagged
    indices = {(p[0], p[1]) for p in pairs}
    assert (0, 1) in indices


def test_find_duplicate_pairs_skips_suppressed():
    from ankithis_api.services.stages.dedup import find_duplicate_pairs

    cards = [
        {"front": "The mitochondria is the powerhouse of the cell.", "back": "A"},
        {"front": "The mitochondria is the powerhouse of the cell.", "back": "B", "suppressed": True},
    ]
    pairs = find_duplicate_pairs(cards)
    assert len(pairs) == 0


@patch("ankithis_api.services.stages.dedup.structured_call")
def test_resolve_duplicates(mock_call):
    mock_call.return_value = {
        "results": [
            {"pair_index": 0, "action": "keep_first", "merged_front": "", "merged_back": ""}
        ]
    }

    from ankithis_api.services.stages.dedup import resolve_duplicates

    cards = [
        {"front": "Card A", "back": "A"},
        {"front": "Card A duplicate", "back": "A"},
    ]
    decisions = resolve_duplicates(cards, [(0, 1, 0.95)])
    assert len(decisions) == 1
    assert decisions[0]["action"] == "keep_first"


def test_apply_dedup_keep_first():
    from ankithis_api.services.stages.dedup import apply_dedup

    cards = [
        {"front": "Card A", "back": "A"},
        {"front": "Card A dup", "back": "A"},
    ]
    decisions = [{"pair_index": 0, "action": "keep_first", "merged_front": "", "merged_back": ""}]
    result = apply_dedup(cards, [(0, 1, 0.9)], decisions)
    assert not result[0].get("suppressed")
    assert result[1]["suppressed"] is True
    assert result[1]["duplicate_of"] == 0


def test_apply_dedup_merge():
    from ankithis_api.services.stages.dedup import apply_dedup

    cards = [
        {"front": "Card A front", "back": "A back"},
        {"front": "Card B front", "back": "B back"},
    ]
    decisions = [{"pair_index": 0, "action": "merge", "merged_front": "Merged front", "merged_back": "Merged back"}]
    result = apply_dedup(cards, [(0, 1, 0.9)], decisions)
    assert result[0]["front"] == "Merged front"
    assert result[0]["back"] == "Merged back"
    assert result[1]["suppressed"] is True
