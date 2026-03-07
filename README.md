# ankithis

Extract core principles and ideas from PDFs and generate high-quality cloze-style Anki flashcard decks.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
uvicorn ankithis.app:app --reload
```

Then upload a PDF at `http://localhost:8000/docs`.

## License

MIT
