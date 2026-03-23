"""Export cards to CSV and APKG formats."""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import tempfile

logger = logging.getLogger(__name__)


def _stable_id(name: str) -> int:
    """Deterministic model/deck ID from a name string (collision-resistant)."""
    return int(hashlib.sha256(name.encode()).hexdigest()[:10], 16) % (2**31)


# Stable model IDs — deterministic across sessions and machines
BASIC_MODEL_ID = _stable_id("AnkiThis Basic v1")
CLOZE_MODEL_ID = _stable_id("AnkiThis Cloze v1")


def export_csv(cards: list[dict]) -> bytes:
    """Export cards to CSV format. Returns UTF-8 bytes."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["front", "back", "card_type", "tags"])

    for card in cards:
        if card.get("suppressed"):
            continue
        writer.writerow(
            [
                card["front"],
                card.get("back", ""),
                card.get("card_type", "basic"),
                card.get("tags", ""),
            ]
        )

    return output.getvalue().encode("utf-8")


CARD_CSS = """\
.card {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 18px;
  line-height: 1.6;
  padding: 20px;
  text-align: left;
  color: #1a1a2e;
  background: #faf8f5;
}
.night_mode .card {
  color: #e0d5c5;
  background: #1a1a2e;
}
.cloze {
  font-weight: bold;
  color: #3a86a8;
}
hr#answer {
  border: none;
  border-top: 1px solid #ddd;
  margin: 16px 0;
}
"""


def export_apkg(cards: list[dict], deck_name: str = "AnkiThis Deck") -> bytes:
    """Export cards to APKG format using genanki. Returns binary APKG data."""
    import genanki

    basic_model = genanki.Model(
        BASIC_MODEL_ID,
        "AnkiThis Basic",
        fields=[
            {"name": "Front"},
            {"name": "Back"},
        ],
        templates=[
            {
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
            },
        ],
        css=CARD_CSS,
    )

    cloze_model = genanki.Model(
        CLOZE_MODEL_ID,
        "AnkiThis Cloze",
        fields=[
            {"name": "Text"},
            {"name": "Extra"},
        ],
        templates=[
            {
                "name": "Cloze",
                "qfmt": "{{cloze:Text}}",
                "afmt": "{{cloze:Text}}<br>{{Extra}}",
            },
        ],
        model_type=genanki.Model.CLOZE,
        css=CARD_CSS,
    )

    deck = genanki.Deck(
        deck_id=_stable_id(deck_name) % (10**10),
        name=deck_name,
    )

    for card in cards:
        if card.get("suppressed"):
            continue

        tags = [t.strip().replace(" ", "_") for t in card.get("tags", "").split(",") if t.strip()]

        if card.get("card_type") == "cloze":
            note = genanki.Note(
                model=cloze_model,
                fields=[card["front"], card.get("back", "")],
                tags=tags,
            )
        else:
            note = genanki.Note(
                model=basic_model,
                fields=[card["front"], card.get("back", "")],
                tags=tags,
            )

        deck.add_note(note)

    # Write to temp file and read back
    with tempfile.NamedTemporaryFile(suffix=".apkg", delete=True) as tmp:
        package = genanki.Package(deck)
        package.write_to_file(tmp.name)
        tmp.seek(0)
        return tmp.read()
