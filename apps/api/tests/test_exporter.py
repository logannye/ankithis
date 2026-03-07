"""Tests for CSV and APKG exporters."""

import csv
import io

from ankithis_api.services.exporter import export_csv


def test_export_csv_basic():
    cards = [
        {
            "front": "What is ATP?",
            "back": "Adenosine triphosphate",
            "card_type": "basic",
            "tags": "biology",
        },
        {
            "front": "{{c1::Mitochondria}} produce ATP.",
            "back": "",
            "card_type": "cloze",
            "tags": "biology,cell",
        },
    ]
    result = export_csv(cards)
    assert isinstance(result, bytes)

    reader = csv.reader(io.StringIO(result.decode("utf-8")))
    rows = list(reader)
    assert rows[0] == ["front", "back", "card_type", "tags"]
    assert len(rows) == 3  # header + 2 cards
    assert rows[1][0] == "What is ATP?"


def test_export_csv_skips_suppressed():
    cards = [
        {"front": "Good card", "back": "Answer", "card_type": "basic", "tags": ""},
        {
            "front": "Bad card",
            "back": "Answer",
            "card_type": "basic",
            "tags": "",
            "suppressed": True,
        },
    ]
    result = export_csv(cards)
    reader = csv.reader(io.StringIO(result.decode("utf-8")))
    rows = list(reader)
    assert len(rows) == 2  # header + 1 active card


def test_export_csv_empty():
    result = export_csv([])
    reader = csv.reader(io.StringIO(result.decode("utf-8")))
    rows = list(reader)
    assert len(rows) == 1  # header only


def test_export_apkg():
    """Test APKG export (requires genanki)."""
    try:
        from ankithis_api.services.exporter import export_apkg
    except ImportError:
        import pytest

        pytest.skip("genanki not installed")

    cards = [
        {
            "front": "What is ATP?",
            "back": "Adenosine triphosphate",
            "card_type": "basic",
            "tags": "biology",
        },
        {
            "front": "{{c1::Mitochondria}} produce ATP.",
            "back": "",
            "card_type": "cloze",
            "tags": "biology",
        },
    ]
    result = export_apkg(cards, deck_name="Test Deck")
    assert isinstance(result, bytes)
    assert len(result) > 0
    # APKG is a zip file, check magic bytes
    assert result[:2] == b"PK"


def test_export_apkg_skips_suppressed():
    try:
        from ankithis_api.services.exporter import export_apkg
    except ImportError:
        import pytest

        pytest.skip("genanki not installed")

    cards = [
        {
            "front": "Good card question for testing",
            "back": "Answer",
            "card_type": "basic",
            "tags": "",
        },
        {
            "front": "Bad card",
            "back": "Answer",
            "card_type": "basic",
            "tags": "",
            "suppressed": True,
        },
    ]
    result = export_apkg(cards)
    assert isinstance(result, bytes)
    assert len(result) > 0
