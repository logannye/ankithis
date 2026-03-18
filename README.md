# AnkiThis

Convert any educational document or YouTube video into a high-quality, study-ready Anki flashcard deck.

AnkiThis uses an adaptive AI pipeline to read your content, classify it, identify the most important concepts, and generate cloze-deletion and Q&A flashcards optimized for long-term retention. Upload a PDF, DOCX, TXT, Markdown file, or paste a YouTube URL and get back a polished `.apkg` deck you can import directly into [Anki](https://apps.ankiweb.net/).

## How It Works

AnkiThis runs an eight-stage adaptive pipeline that adapts to your content type:

1. **Parse & Structure** — Extracts text from your document or YouTube transcript, detects section boundaries, and splits content into semantically-aligned chunks.
2. **Content Classification (Stage 0)** — An LLM classifies your content across 6 dimensions: content type, domain, difficulty, information density, structure quality, and knowledge type. This produces a Content Profile that adapts every downstream stage.
3. **Section Annotation** — Each section is tagged with its pedagogical function (definitions, theory, methodology, examples, etc.) using fast heuristics.
4. **Concept Extraction** — Profile-aware prompts extract concepts tailored to the content type: claims + evidence for research papers, bullet expansions for lecture slides, prerequisite gaps for personal notes.
5. **Concept Merge** — Duplicates are merged with content-aware aggressiveness: heavy dedup for slides, light for research papers.
6. **Card Planning** — Density targets adapt to information density (sparse content gets more cards per word, dense content gets fewer). Card type ratios adjust per section function.
7. **Card Generation** — Difficulty-aware prompts with 5 embedded pedagogical principles ensure every card tests understanding, not just recognition.
8. **Quality Control** — AI critique with content-type quality bars (strict for research papers, lenient for personal notes) + deterministic anti-pattern detection (trivia, verbatim, ambiguous cloze, compound questions).

The result is a deck that matches your content, not a one-size-fits-all dump.

## Features

- **Multi-format support** — PDF, DOCX, TXT, Markdown, and YouTube videos
- **Adaptive intelligence** — Content classification automatically adjusts the entire pipeline
- **YouTube integration** — Paste a URL, get cards from transcript + visual content
- **Visual analysis** — For video content, intelligent frame sampling detects when visuals carry information beyond the transcript
- **Configurable generation** — Choose your study goal, card style, and deck size
- **Two card types** — Cloze deletions for terminology, Q&A for mechanisms and comparisons
- **Quality pipeline** — AI critique + 5 deterministic anti-pattern filters catch bad cards
- **Review before export** — Preview cards, remove ones you don't want, regenerate with different settings
- **Anki-ready export** — Download as `.apkg` (native Anki package) or CSV

## Adaptive Intelligence

AnkiThis classifies every input and adapts its behavior:

| Content Type | Extraction Focus | Chunk Size | Merge Style | Quality Bar |
|-------------|-----------------|------------|-------------|-------------|
| Lecture slides | Bullet expansions, cross-slide relationships | 30-400 words | Aggressive | Moderate |
| Research papers | Claims + evidence, limitations | 600-2000 words | Light | Strict |
| Textbook chapters | Definitions, theory, procedures | 1000-2000 words | Moderate | Moderate |
| Personal notes | Prerequisite gaps, user's framing | 200-800 words | Very light | Lenient |
| Technical docs | API behaviors, gotchas, trade-offs | 400-1200 words | Moderate | Strict |
| General articles | Argument structure, evidence | 800-1600 words | Moderate | Moderate |
| YouTube videos | Transcript + visual content | 600-1400 words | Moderate | Moderate |

## YouTube Support

Paste a YouTube URL and AnkiThis will:

1. **Fetch metadata** — Title, channel, duration, chapter markers
2. **Extract transcript** — Manual captions preferred, auto-generated fallback
3. **Assess visual density** — 6 sample frames determine if visuals carry important information
4. **Sample key frames** — Scene detection extracts frames at transitions (slides, whiteboard changes)
5. **Analyze frames** — Multimodal LLM extracts visual information not captured in the transcript
6. **Section by chapters** — YouTube chapter markers become section boundaries, with topic-shift fallback

Duration limits: up to 3 hours. Videos over 90 minutes show a warning. Chapter selection available when the creator added chapter markers.

## Configuration Options

| Option | Values | Description |
|--------|--------|-------------|
| Study Goal | Free text (optional) | e.g. "Prepare for organic chemistry midterm" |
| Card Style | `cloze_heavy`, `qa_heavy`, `balanced` | Preferred card format (treated as a bias, not absolute) |
| Deck Size | `small`, `medium`, `large` | Card density, adapted by content information density |

Deck size uses adaptive density scaled by content type. A sparse lecture deck on "Fewer" gets 1.5x the base density; a dense research paper on "More" gets 0.6x. Floor: 5 cards, ceiling: 300.

## Tech Stack

- **Backend**: Python, FastAPI, Celery, SQLAlchemy
- **Frontend**: Next.js 16, TypeScript, Tailwind CSS 4
- **Database**: PostgreSQL 16
- **Queue**: Redis 7 + Celery
- **LLM**: Kimi K2.5 via AWS Bedrock Converse API (multimodal)
- **Video**: yt-dlp, ffmpeg (scene detection + frame extraction)
- **Export**: genanki (`.apkg`), CSV

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- AWS credentials with Bedrock access (for Kimi K2.5)
- ffmpeg (for YouTube visual analysis)

### Setup

```bash
# Clone the repo
git clone https://github.com/logannye/ankithis.git
cd ankithis

# Create your environment file
cp .env.example .env
# Edit .env and add your AWS credentials:
#   ANKITHIS_AWS_ACCESS_KEY_ID=...
#   ANKITHIS_AWS_SECRET_ACCESS_KEY=...
#   ANKITHIS_AWS_REGION=us-west-2

# Start all services
make up

# Run database migrations
make migrate
```

The API will be available at `http://localhost:8000` and the web UI at `http://localhost:3000`.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Create an account |
| `POST` | `/api/auth/login` | Sign in and get a token |
| `POST` | `/api/upload` | Upload a document (PDF/DOCX/TXT/MD) |
| `POST` | `/api/youtube/preview` | Preview YouTube video metadata |
| `POST` | `/api/youtube` | Process a YouTube URL |
| `POST` | `/api/documents/{id}/generate` | Start card generation |
| `GET` | `/api/jobs/{id}` | Poll generation progress |
| `GET` | `/api/documents/{id}/review` | Review generated cards |
| `POST` | `/api/cards/{id}/remove` | Remove a card from the deck |
| `POST` | `/api/documents/{id}/regenerate` | Regenerate with new settings |
| `GET` | `/api/documents/{id}/export/apkg` | Download Anki package |
| `GET` | `/api/documents/{id}/export/csv` | Download CSV |

All endpoints except auth require a Bearer token in the `Authorization` header.

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
│   │   │   ├── config.py       # Settings (env-based, Bedrock credentials)
│   │   │   ├── models/         # SQLAlchemy models (Document, ContentProfile, VideoSource, Card, etc.)
│   │   │   ├── routers/        # API route handlers (upload, youtube, generate, review, export)
│   │   │   ├── services/
│   │   │   │   ├── pipeline.py         # 8-stage orchestrator
│   │   │   │   ├── parser.py           # Document parsing dispatcher
│   │   │   │   ├── chunker.py          # Adaptive chunking (9 content-type profiles)
│   │   │   │   ├── section_annotator.py # Heuristic pedagogical function tagging
│   │   │   │   ├── qc.py              # Quality control (structural + anti-pattern)
│   │   │   │   ├── exporter.py        # CSV and APKG export
│   │   │   │   ├── stages/            # Pipeline stage implementations (0, A-F)
│   │   │   │   └── youtube/           # YouTube intake (metadata, transcript, frames, sectioning)
│   │   │   └── llm/
│   │   │       ├── client.py          # Bedrock Converse API (multimodal image support)
│   │   │       ├── schemas.py         # Pydantic models for all stages
│   │   │       └── prompts/           # Adaptive prompt templates (stage_0 through stage_f)
│   │   ├── alembic/            # Database migrations
│   │   └── tests/              # 134+ unit tests
│   └── web/                    # Next.js frontend
│       └── src/
│           ├── app/            # Pages (upload, processing, review, login)
│           └── lib/            # API client, types, auth hooks
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Best Results

AnkiThis works best with:
- Textbook chapters and academic material (10-80 pages)
- Lecture slides and presentation exports
- Research papers and journal articles
- Personal study notes and class notes
- Technical documentation and API references
- Educational YouTube videos (with captions)

## License

MIT
