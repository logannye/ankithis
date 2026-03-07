# AnkiThis

Convert any educational document into a high-quality, study-ready Anki flashcard deck.

AnkiThis uses a multi-pass AI pipeline to read your documents, identify the most important concepts, and generate cloze-deletion and Q&A flashcards optimized for long-term retention. Upload a PDF, DOCX, TXT, or Markdown file and get back a polished `.apkg` deck you can import directly into [Anki](https://apps.ankiweb.net/).

## How It Works

AnkiThis runs a six-stage pipeline designed to produce cards of pedagogical value that you'd actually want to study:

1. **Parse & Structure** — Extracts text from your document, detects section boundaries, and splits content into manageable chunks.
2. **Concept Extraction** — An LLM identifies key concepts, definitions, mechanisms, and relationships in each chunk.
3. **Concept Merge** — Duplicate and overlapping concepts are merged across sections. Concepts are ranked by importance.
4. **Card Planning** — The system decides which concepts deserve cards, what card type to use (cloze vs. Q&A), and how many cards to generate based on your preferences.
5. **Card Generation** — High-quality flashcards are generated with precise cloze deletions (1–4 word blanks) and clear Q&A pairs.
6. **Quality Control** — A critique pass rewrites weak cards, deduplicates near-identical ones, and suppresses anything that doesn't meet the quality bar.

The result is a compact, curated deck — not a bloated dump of every sentence in your textbook.

## Features

- **Multi-format support** — PDF, DOCX, TXT, and Markdown
- **Configurable generation** — Choose your study goal, card style, and deck size
- **Two card types** — Cloze deletions for terminology and definitions, Q&A for mechanisms and comparisons
- **Quality pipeline** — AI-powered critique + deterministic filters catch bad cards before they reach your deck
- **Review before export** — Preview cards, remove ones you don't want, regenerate with different settings
- **Anki-ready export** — Download as `.apkg` (native Anki package) or CSV

## Configuration Options

| Option | Values | Description |
|--------|--------|-------------|
| Study Goal | `exam_essentials`, `balanced_mastery`, `comprehensive` | How much material to cover |
| Card Style | `mostly_cloze`, `mixed`, `mostly_qa` | Preferred card format |
| Deck Size | `small`, `medium`, `large` | Target number of cards |
| Scope | `full_document`, `selected_pages` | Process entire file or a page range |

## Tech Stack

- **Backend**: Python, FastAPI, Celery, SQLAlchemy
- **Frontend**: Next.js, TypeScript, Tailwind CSS
- **Database**: PostgreSQL
- **Queue**: Redis + Celery
- **LLM**: Anthropic Claude API
- **Export**: genanki (`.apkg`), CSV

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An [Anthropic API key](https://console.anthropic.com/)

### Setup

```bash
# Clone the repo
git clone https://github.com/logannye/ankithis.git
cd ankithis

# Create your environment file
cp .env.example .env
# Edit .env and add your ANKITHIS_ANTHROPIC_API_KEY

# Start all services
make up

# Run database migrations
make migrate
```

The API will be available at `http://localhost:8000` and the web UI at `http://localhost:3000`.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload a document |
| `POST` | `/api/documents/{id}/generate` | Start card generation |
| `GET` | `/api/jobs/{id}` | Poll generation progress |
| `GET` | `/api/documents/{id}/review` | Review generated cards |
| `POST` | `/api/cards/{id}/remove` | Remove a card from the deck |
| `POST` | `/api/documents/{id}/regenerate` | Regenerate with new settings |
| `GET` | `/api/documents/{id}/export/apkg` | Download Anki package |
| `GET` | `/api/documents/{id}/export/csv` | Download CSV |

Interactive API docs are available at `http://localhost:8000/docs`.

### Development

```bash
# Run backend tests
make test-api

# Lint backend code
make lint

# View logs
make logs

# Open a database shell
make shell-db
```

## Project Structure

```
ankithis/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── src/ankithis_api/
│   │   │   ├── app.py          # FastAPI application
│   │   │   ├── config.py       # Settings (env-based)
│   │   │   ├── db.py           # Database engine
│   │   │   ├── worker.py       # Celery worker
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── routers/        # API route handlers
│   │   │   ├── schemas/        # Pydantic request/response schemas
│   │   │   ├── services/       # Business logic + pipeline stages
│   │   │   └── llm/            # LLM client + prompt templates
│   │   ├── alembic/            # Database migrations
│   │   └── tests/
│   └── web/                    # Next.js frontend
│       └── src/app/
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Best Results

AnkiThis works best with:
- Digital textbook chapters (10–80 pages)
- Typed lecture notes and study guides
- Review articles and explanatory writing
- Reasonably structured documents with headings

It is not designed for handwritten notes, image-heavy slides, or scanned documents with poor OCR quality.

## License

MIT
