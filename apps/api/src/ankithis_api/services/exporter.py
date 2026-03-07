"""Export cards to CSV and APKG formats."""

from __future__ import annotations

import csv
import io
import logging
import tempfile

logger = logging.getLogger(__name__)

# Fixed model IDs for genanki — must stay constant across exports
BASIC_MODEL_ID = 1607392319
CLOZE_MODEL_ID = 1607392320


def export_csv(cards: list[dict]) -> bytes:
    """Export cards to CSV format. Returns UTF-8 bytes."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["front", "back", "card_type", "tags"])

    for card in cards:
        if card.get("suppressed"):
            continue
        writer.writerow([
            card["front"],
            card.get("back", ""),
            card.get("card_type", "basic"),
            card.get("tags", ""),
        ])

    return output.getvalue().encode("utf-8")


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
    )

    deck = genanki.Deck(
        deck_id=abs(hash(deck_name)) % (10**10),
        name=deck_name,
    )

    for card in cards:
        if card.get("suppressed"):
            continue

        tags = [t.strip() for t in card.get("tags", "").split(",") if t.strip()]

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
