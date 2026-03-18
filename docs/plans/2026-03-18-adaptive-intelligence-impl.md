# Adaptive Intelligence Engine — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a pre-pipeline content classification layer, adaptive chunking, per-stage prompt adaptation, YouTube video intake, and pedagogical quality enforcement to AnkiThis.

**Architecture:** Stage 0 (Content Intelligence) runs before the existing 6-stage pipeline. It classifies input at document/section/chunk levels, producing a ContentProfile that parameterizes all downstream stages. YouTube intake is a separate pre-processing path that converges to the same ContentProfile + Chunks interface. The existing Stages A-F are modified to read the profile and adapt their prompts, not replaced.

**Tech Stack:** FastAPI, SQLAlchemy (PostgreSQL), Celery, Kimi K2.5 via AWS Bedrock (multimodal), yt-dlp (YouTube), Next.js 16 (TypeScript), Tailwind CSS 4.

**Design Doc:** `docs/plans/2026-03-18-adaptive-intelligence-design.md`

---

## Phase 1: Database Schema & Models (foundation)

### Task 1: Add new enums to models/enums.py

**Files:**
- Modify: `apps/api/src/ankithis_api/models/enums.py`
- Test: `apps/api/tests/test_enums.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_enums.py
from ankithis_api.models.enums import (
    ContentType, Difficulty, InformationDensity, StructureQuality,
    KnowledgeType, PedagogicalFunction, VisualDensity, VideoType, FileType,
)

def test_content_type_values():
    assert ContentType.LECTURE_SLIDES == "lecture_slides"
    assert ContentType.RESEARCH_PAPER == "research_paper"
    assert ContentType.TEXTBOOK_CHAPTER == "textbook_chapter"
    assert ContentType.PERSONAL_NOTES == "personal_notes"
    assert ContentType.TECHNICAL_DOCS == "technical_docs"
    assert ContentType.GENERAL_ARTICLE == "general_article"
    assert ContentType.VIDEO_LECTURE == "video_lecture"
    assert ContentType.VIDEO_TUTORIAL == "video_tutorial"
    assert ContentType.VIDEO_DEMO == "video_demo"

def test_difficulty_values():
    assert Difficulty.INTRODUCTORY == "introductory"
    assert Difficulty.EXPERT == "expert"

def test_information_density_values():
    assert InformationDensity.SPARSE == "sparse"
    assert InformationDensity.VERY_DENSE == "very_dense"

def test_structure_quality_values():
    assert StructureQuality.WELL_STRUCTURED == "well_structured"
    assert StructureQuality.UNSTRUCTURED == "unstructured"

def test_knowledge_type_values():
    assert KnowledgeType.FACTUAL == "factual"
    assert KnowledgeType.MIXED == "mixed"

def test_pedagogical_function_values():
    assert PedagogicalFunction.DEFINITIONS == "definitions"
    assert PedagogicalFunction.THEORY == "theory"
    assert PedagogicalFunction.METHODOLOGY == "methodology"
    assert PedagogicalFunction.EXAMPLES == "examples"
    assert PedagogicalFunction.DATA_RESULTS == "data_results"
    assert PedagogicalFunction.SUMMARY == "summary"
    assert PedagogicalFunction.CODE == "code"
    assert PedagogicalFunction.ENUMERATION == "enumeration"
    assert PedagogicalFunction.UNKNOWN == "unknown"

def test_visual_density_values():
    assert VisualDensity.LOW == "low"
    assert VisualDensity.HIGH == "high"

def test_video_type_values():
    assert VideoType.TALKING_HEAD == "talking_head"
    assert VideoType.SLIDES_WITH_SPEAKER == "slides_with_speaker"

def test_file_type_includes_youtube():
    assert FileType.YOUTUBE == "youtube"
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_enums.py -v`
Expected: ImportError — new enums don't exist yet

**Step 3: Write the implementation**

Add these enums after the existing ones in `apps/api/src/ankithis_api/models/enums.py`:

```python
class ContentType(str, enum.Enum):
    LECTURE_SLIDES = "lecture_slides"
    RESEARCH_PAPER = "research_paper"
    TEXTBOOK_CHAPTER = "textbook_chapter"
    PERSONAL_NOTES = "personal_notes"
    TECHNICAL_DOCS = "technical_docs"
    GENERAL_ARTICLE = "general_article"
    VIDEO_LECTURE = "video_lecture"
    VIDEO_TUTORIAL = "video_tutorial"
    VIDEO_DEMO = "video_demo"

class Difficulty(str, enum.Enum):
    INTRODUCTORY = "introductory"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class InformationDensity(str, enum.Enum):
    SPARSE = "sparse"
    MODERATE = "moderate"
    DENSE = "dense"
    VERY_DENSE = "very_dense"

class StructureQuality(str, enum.Enum):
    WELL_STRUCTURED = "well_structured"
    SEMI_STRUCTURED = "semi_structured"
    UNSTRUCTURED = "unstructured"

class KnowledgeType(str, enum.Enum):
    FACTUAL = "factual"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    MIXED = "mixed"

class PedagogicalFunction(str, enum.Enum):
    DEFINITIONS = "definitions"
    THEORY = "theory"
    METHODOLOGY = "methodology"
    EXAMPLES = "examples"
    DATA_RESULTS = "data_results"
    SUMMARY = "summary"
    CODE = "code"
    ENUMERATION = "enumeration"
    UNKNOWN = "unknown"

class VisualDensity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class VideoType(str, enum.Enum):
    TALKING_HEAD = "talking_head"
    SLIDES_WITH_SPEAKER = "slides_with_speaker"
    SCREENCAST = "screencast"
    WHITEBOARD = "whiteboard"
    ANIMATION = "animation"
    DEMONSTRATION = "demonstration"
    MIXED = "mixed"
```

Also add `YOUTUBE = "youtube"` to the existing `FileType` enum.

**Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_enums.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/models/enums.py apps/api/tests/test_enums.py
git commit -m "feat: add enums for content classification, pedagogy, and video types"
```

---

### Task 2: Add ContentProfile and VideoSource models

**Files:**
- Create: `apps/api/src/ankithis_api/models/content_profile.py`
- Create: `apps/api/src/ankithis_api/models/video_source.py`
- Modify: `apps/api/src/ankithis_api/models/__init__.py` (add imports)
- Modify: `apps/api/src/ankithis_api/models/document.py` (add columns to Section and Chunk)
- Test: `apps/api/tests/test_models_profile.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_models_profile.py
from ankithis_api.models.content_profile import ContentProfile
from ankithis_api.models.video_source import VideoSource
from ankithis_api.models.document import Section, Chunk

def test_content_profile_has_columns():
    cols = {c.name for c in ContentProfile.__table__.columns}
    assert "content_type" in cols
    assert "domain" in cols
    assert "difficulty" in cols
    assert "information_density" in cols
    assert "structure_quality" in cols
    assert "primary_knowledge_type" in cols
    assert "recommended_cloze_ratio" in cols
    assert "recommended_qa_ratio" in cols
    assert "special_considerations" in cols
    assert "document_id" in cols

def test_video_source_has_columns():
    cols = {c.name for c in VideoSource.__table__.columns}
    assert "youtube_url" in cols
    assert "video_id" in cols
    assert "title" in cols
    assert "channel" in cols
    assert "duration_seconds" in cols
    assert "visual_density" in cols
    assert "video_type" in cols
    assert "chapter_markers" in cols
    assert "document_id" in cols

def test_section_has_pedagogical_function():
    cols = {c.name for c in Section.__table__.columns}
    assert "pedagogical_function" in cols

def test_chunk_has_visual_context():
    cols = {c.name for c in Chunk.__table__.columns}
    assert "visual_context" in cols
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_models_profile.py -v`
Expected: ImportError

**Step 3: Write the implementation**

Create `apps/api/src/ankithis_api/models/content_profile.py`:

```python
"""ContentProfile — document-level classification from Stage 0."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON

from ankithis_api.models.base import Base, UUIDMixin, TimestampMixin
from ankithis_api.models.enums import (
    ContentType, Difficulty, InformationDensity,
    StructureQuality, KnowledgeType,
)


class ContentProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "content_profiles"

    document_id = sa.Column(
        sa.UUID, ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    content_type = sa.Column(sa.Enum(ContentType), nullable=False)
    domain = sa.Column(sa.String(200), nullable=False, default="general")
    difficulty = sa.Column(sa.Enum(Difficulty), nullable=False, default=Difficulty.INTERMEDIATE)
    information_density = sa.Column(
        sa.Enum(InformationDensity), nullable=False, default=InformationDensity.MODERATE,
    )
    structure_quality = sa.Column(
        sa.Enum(StructureQuality), nullable=False, default=StructureQuality.SEMI_STRUCTURED,
    )
    primary_knowledge_type = sa.Column(
        sa.Enum(KnowledgeType), nullable=False, default=KnowledgeType.MIXED,
    )
    recommended_cloze_ratio = sa.Column(sa.Float, nullable=False, default=0.5)
    recommended_qa_ratio = sa.Column(sa.Float, nullable=False, default=0.5)
    special_considerations = sa.Column(JSON, nullable=False, server_default="[]")
```

Create `apps/api/src/ankithis_api/models/video_source.py`:

```python
"""VideoSource — metadata for YouTube-sourced documents."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON

from ankithis_api.models.base import Base, UUIDMixin, TimestampMixin
from ankithis_api.models.enums import VisualDensity, VideoType


class VideoSource(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "video_sources"

    document_id = sa.Column(
        sa.UUID, ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    youtube_url = sa.Column(sa.String(500), nullable=False)
    video_id = sa.Column(sa.String(20), nullable=False)
    title = sa.Column(sa.String(500), nullable=False)
    channel = sa.Column(sa.String(200), nullable=True)
    duration_seconds = sa.Column(sa.Integer, nullable=False)
    has_manual_captions = sa.Column(sa.Boolean, nullable=False, default=False)
    visual_density = sa.Column(sa.Enum(VisualDensity), nullable=True)
    video_type = sa.Column(sa.Enum(VideoType), nullable=True)
    chapter_markers = sa.Column(JSON, nullable=False, server_default="[]")
```

Modify `apps/api/src/ankithis_api/models/document.py` — add to Section class:

```python
pedagogical_function = sa.Column(
    sa.Enum(PedagogicalFunction), nullable=True, default=None,
)
```

Modify Chunk class — add:

```python
visual_context = sa.Column(sa.Text, nullable=True, default=None)
```

Add imports to `models/__init__.py`.

**Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_models_profile.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/models/
git add apps/api/tests/test_models_profile.py
git commit -m "feat: add ContentProfile, VideoSource models; extend Section and Chunk"
```

---

### Task 3: Create Alembic migration for new schema

**Files:**
- Create: `apps/api/alembic/versions/003_adaptive_intelligence.py`

**Step 1: Generate migration**

Run: `cd apps/api && alembic revision --autogenerate -m "add adaptive intelligence tables"`

**Step 2: Review and hand-edit if needed**

The migration should create `content_profiles`, `video_sources` tables and add `pedagogical_function` to `sections`, `visual_context` to `chunks`, `youtube` to `file_type` enum.

**Step 3: Run migration**

Run: `cd apps/api && alembic upgrade head`
Expected: Tables created successfully

**Step 4: Commit**

```bash
git add apps/api/alembic/
git commit -m "feat: migration 003 — adaptive intelligence schema"
```

---

## Phase 2: Stage 0 — Content Classification

### Task 4: Classification LLM prompt and schema

**Files:**
- Create: `apps/api/src/ankithis_api/llm/prompts/stage_0.py`
- Modify: `apps/api/src/ankithis_api/llm/schemas.py` (add ClassificationOutput)
- Test: `apps/api/tests/test_classification_schema.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_classification_schema.py
from ankithis_api.llm.schemas import ClassificationOutput, schema_for

def test_classification_output_validates():
    data = {
        "content_type": "research_paper",
        "domain": "oncology",
        "difficulty": "advanced",
        "information_density": "dense",
        "structure_quality": "well_structured",
        "primary_knowledge_type": "conceptual",
        "recommended_cloze_ratio": 0.4,
        "recommended_qa_ratio": 0.6,
        "special_considerations": ["heavy_notation"],
    }
    output = ClassificationOutput.model_validate(data)
    assert output.content_type == "research_paper"
    assert output.difficulty == "advanced"
    assert output.recommended_cloze_ratio == 0.4

def test_classification_schema_has_required_fields():
    schema = schema_for(ClassificationOutput)
    props = schema["properties"]
    assert "content_type" in props
    assert "domain" in props
    assert "difficulty" in props
    assert "special_considerations" in props
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_classification_schema.py -v`
Expected: ImportError

**Step 3: Write the implementation**

Add to `apps/api/src/ankithis_api/llm/schemas.py` (after existing schemas):

```python
class ClassificationOutput(BaseModel):
    content_type: str  # matches ContentType enum values
    domain: str
    difficulty: str  # matches Difficulty enum values
    information_density: str  # matches InformationDensity enum values
    structure_quality: str  # matches StructureQuality enum values
    primary_knowledge_type: str  # matches KnowledgeType enum values
    recommended_cloze_ratio: float
    recommended_qa_ratio: float
    special_considerations: list[str]
```

Create `apps/api/src/ankithis_api/llm/prompts/stage_0.py`:

```python
"""Stage 0: Content Classification — identify content type and characteristics."""

SYSTEM = """\
You are an expert educational content analyst. Given a sample of a document, \
classify it along several dimensions to help downstream systems generate \
optimal flashcards.

Content types:
- lecture_slides: Sparse, bullet-heavy, one idea per slide
- research_paper: Dense, structured (abstract/methods/results/discussion)
- textbook_chapter: Hierarchical, definitions + theory + examples
- personal_notes: Informal, abbreviated, variable quality
- technical_docs: API references, how-to guides, code-heavy
- general_article: Narrative non-fiction, essays, blog posts
- video_lecture: Transcript from an educational lecture video
- video_tutorial: Transcript from a step-by-step tutorial video
- video_demo: Transcript from a demonstration or lab video

Difficulty levels:
- introductory: Assumes no prior knowledge, defines all terms
- intermediate: Assumes foundational vocabulary, builds on basics
- advanced: Assumes domain fluency, covers nuance and edge cases
- expert: Frontier material, novel findings, methodology critiques

Information density:
- sparse: Few concepts per page (slides, brief notes)
- moderate: Standard density (articles, textbooks)
- dense: High concept density (technical docs, detailed textbooks)
- very_dense: Extremely packed (research papers, reference material)

Knowledge types:
- factual: Primarily facts, definitions, data
- conceptual: Primarily theories, mechanisms, relationships
- procedural: Primarily steps, processes, how-to
- mixed: Combination of above

Special considerations (include all that apply):
- heavy_notation: Math, chemistry, or formal notation
- code_examples: Programming code present
- visual_diagrams_referenced: References to figures/diagrams
- foreign_language_terms: Non-English terminology
- clinical_data: Patient data, trial results
- historical_dates: Chronological events
- legal_citations: Legal references
"""

USER_TEMPLATE = """\
Classify this document. Here is a sample:

--- HEADINGS ---
{headings}

--- OPENING TEXT (first ~2000 words) ---
{opening_text}

--- CLOSING TEXT (last ~500 words) ---
{closing_text}

Return your classification as a JSON object.
"""
```

**Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_classification_schema.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/llm/prompts/stage_0.py
git add apps/api/src/ankithis_api/llm/schemas.py
git add apps/api/tests/test_classification_schema.py
git commit -m "feat: Stage 0 classification prompt and schema"
```

---

### Task 5: Section annotation heuristic

**Files:**
- Create: `apps/api/src/ankithis_api/services/section_annotator.py`
- Test: `apps/api/tests/test_section_annotator.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_section_annotator.py
from ankithis_api.services.section_annotator import annotate_section

def test_definitions_section():
    assert annotate_section("Key Definitions", "A receptor is defined as a protein...") == "definitions"

def test_methodology_section():
    assert annotate_section("Methods", "The protocol involves three steps...") == "methodology"

def test_theory_section():
    assert annotate_section("Theoretical Framework", "The mechanism by which...") == "theory"

def test_examples_section():
    assert annotate_section("Case Study: Patient X", "Consider the following example...") == "examples"

def test_data_results_section():
    assert annotate_section("Results", "Figure 3 shows that p < 0.01...") == "data_results"

def test_summary_section():
    assert annotate_section("Summary", "In summary, the key takeaways are...") == "summary"

def test_code_section():
    assert annotate_section("Implementation", "```python\ndef calculate():...") == "code"

def test_enumeration_section():
    assert annotate_section("Properties of Enzymes", "- High specificity\n- Catalytic efficiency\n- Regulated activity") == "enumeration"

def test_unknown_fallback():
    assert annotate_section("Chapter 4", "The quick brown fox jumps over the lazy dog.") == "unknown"

def test_none_title():
    assert annotate_section(None, "This is defined as something important.") == "definitions"
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_section_annotator.py -v`
Expected: ImportError

**Step 3: Write the implementation**

```python
# apps/api/src/ankithis_api/services/section_annotator.py
"""Heuristic section-level pedagogical function annotation."""

from __future__ import annotations

import re

# Heading patterns → function
_HEADING_SIGNALS: list[tuple[str, re.Pattern]] = [
    ("definitions", re.compile(r"defini|glossar|terminolog|vocabulary", re.I)),
    ("methodology", re.compile(r"method|protocol|procedure|materials and|experimental setup", re.I)),
    ("data_results", re.compile(r"result|finding|data|figure|table\b|observation", re.I)),
    ("summary", re.compile(r"summar|conclusion|takeaway|key point|recap|review", re.I)),
    ("examples", re.compile(r"example|case stud|scenario|illustration|exercise", re.I)),
    ("theory", re.compile(r"theor|framework|model|mechanism|principle|concept", re.I)),
]

# First-paragraph patterns → function
_BODY_SIGNALS: list[tuple[str, re.Pattern]] = [
    ("definitions", re.compile(r"is defined as|refers to|definition of|meaning of", re.I)),
    ("methodology", re.compile(r"step[s ]?\d|protocol|procedure|the following steps", re.I)),
    ("data_results", re.compile(r"figure \d|table \d|p\s*[<>]\s*0\.\d|statistically significant", re.I)),
    ("summary", re.compile(r"in summary|to summarize|key takeaway|in conclusion", re.I)),
    ("examples", re.compile(r"consider the following|for example|for instance|suppose that", re.I)),
    ("code", re.compile(r"```|def \w+\(|class \w+|function \w+|import \w+", re.I)),
    ("enumeration", re.compile(r"^[\s]*[-•*]\s+\w+.*\n[\s]*[-•*]\s+\w+", re.M)),
    ("theory", re.compile(r"mechanism|principle|model|the relationship between", re.I)),
]


def annotate_section(title: str | None, first_paragraph: str) -> str:
    """Return pedagogical function label for a section.

    Uses heading text first, then falls back to first-paragraph content signals.
    Returns 'unknown' if confidence is low.
    """
    # Check heading signals
    if title:
        for func, pattern in _HEADING_SIGNALS:
            if pattern.search(title):
                return func

    # Check body signals
    text = first_paragraph[:500]  # Only need a small sample
    for func, pattern in _BODY_SIGNALS:
        if pattern.search(text):
            return func

    return "unknown"
```

**Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_section_annotator.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/services/section_annotator.py
git add apps/api/tests/test_section_annotator.py
git commit -m "feat: heuristic section-level pedagogical function annotator"
```

---

### Task 6: Content classifier service (Stage 0 orchestrator)

**Files:**
- Create: `apps/api/src/ankithis_api/services/stages/classification.py`
- Test: `apps/api/tests/test_classification.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_classification.py
from ankithis_api.services.stages.classification import (
    _build_sample, _safe_classify, DEFAULT_PROFILE,
)
from ankithis_api.services.parser import ParsedSection

def test_build_sample_extracts_headings_and_text():
    sections = [
        ParsedSection(title="Introduction", level=1, paragraphs=["First para. " * 200]),
        ParsedSection(title="Methods", level=1, paragraphs=["Method text here."]),
    ]
    headings, opening, closing = _build_sample(sections)
    assert "Introduction" in headings
    assert "Methods" in headings
    assert "First para." in opening
    assert len(opening) <= 12000  # ~2000 words

def test_safe_classify_returns_default_on_failure():
    profile = _safe_classify("", "", "")
    assert profile["content_type"] == DEFAULT_PROFILE["content_type"]
    assert profile["difficulty"] == DEFAULT_PROFILE["difficulty"]

def test_default_profile_has_all_fields():
    assert "content_type" in DEFAULT_PROFILE
    assert "domain" in DEFAULT_PROFILE
    assert "difficulty" in DEFAULT_PROFILE
    assert "information_density" in DEFAULT_PROFILE
    assert "recommended_cloze_ratio" in DEFAULT_PROFILE
    assert "special_considerations" in DEFAULT_PROFILE
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_classification.py -v`
Expected: ImportError

**Step 3: Write the implementation**

```python
# apps/api/src/ankithis_api/services/stages/classification.py
"""Stage 0: Classify document content to produce a ContentProfile."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.stage_0 import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import ClassificationOutput, schema_for
from ankithis_api.services.parser import ParsedSection

logger = logging.getLogger(__name__)

DEFAULT_PROFILE: dict = {
    "content_type": "general_article",
    "domain": "general",
    "difficulty": "intermediate",
    "information_density": "moderate",
    "structure_quality": "semi_structured",
    "primary_knowledge_type": "mixed",
    "recommended_cloze_ratio": 0.5,
    "recommended_qa_ratio": 0.5,
    "special_considerations": [],
}


def _build_sample(
    sections: list[ParsedSection],
) -> tuple[str, str, str]:
    """Extract headings, opening text, and closing text for classification."""
    headings = "\n".join(
        f"{'#' * s.level} {s.title}" for s in sections if s.title
    )

    # Opening: first ~2000 words
    all_text = "\n\n".join(s.text for s in sections)
    words = all_text.split()
    opening = " ".join(words[:2000])

    # Closing: last ~500 words
    closing = " ".join(words[-500:]) if len(words) > 500 else ""

    return headings, opening, closing


def _safe_classify(headings: str, opening: str, closing: str) -> dict:
    """Call LLM for classification, return DEFAULT_PROFILE on any failure."""
    if not opening.strip():
        return dict(DEFAULT_PROFILE)

    try:
        user = USER_TEMPLATE.format(
            headings=headings or "(no headings detected)",
            opening_text=opening[:12000],
            closing_text=closing[:3000],
        )
        result = structured_call(
            system=SYSTEM,
            user=user,
            tool_name="classify_content",
            tool_schema=schema_for(ClassificationOutput),
            model=settings.bedrock_model,
        )
        output = ClassificationOutput.model_validate(result)
        return output.model_dump()
    except Exception:
        logger.warning("Content classification failed, using defaults", exc_info=True)
        return dict(DEFAULT_PROFILE)


def classify_document(sections: list[ParsedSection]) -> dict:
    """Run Stage 0 classification on parsed sections. Returns profile dict."""
    headings, opening, closing = _build_sample(sections)
    return _safe_classify(headings, opening, closing)
```

**Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_classification.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/services/stages/classification.py
git add apps/api/tests/test_classification.py
git commit -m "feat: Stage 0 content classification service"
```

---

### Task 7: Adaptive chunker

**Files:**
- Modify: `apps/api/src/ankithis_api/services/chunker.py`
- Test: `apps/api/tests/test_adaptive_chunker.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_adaptive_chunker.py
from ankithis_api.services.chunker import chunk_section, get_chunk_params

def test_get_chunk_params_lecture_slides():
    params = get_chunk_params("lecture_slides")
    assert params["min_words"] < 800  # Slides: small chunks
    assert params["max_words"] < 1600

def test_get_chunk_params_research_paper():
    params = get_chunk_params("research_paper")
    assert params["min_words"] >= 600
    assert params["max_words"] >= 1600

def test_get_chunk_params_personal_notes():
    params = get_chunk_params("personal_notes")
    assert params["min_words"] <= 400
    assert params["max_words"] <= 800

def test_get_chunk_params_default():
    params = get_chunk_params("general_article")
    assert params["min_words"] == 800
    assert params["max_words"] == 1600

def test_get_chunk_params_unknown_type():
    params = get_chunk_params("unknown_type_xyz")
    assert params["min_words"] == 800  # Falls back to default
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_adaptive_chunker.py -v`
Expected: ImportError on `get_chunk_params`

**Step 3: Write the implementation**

Modify `apps/api/src/ankithis_api/services/chunker.py`. Add `get_chunk_params()` function and modify `chunk_section()` to accept optional min/max overrides:

```python
# Add after existing constants (line 8)
CHUNK_PARAMS_BY_TYPE: dict[str, dict[str, int]] = {
    "lecture_slides": {"min_words": 30, "max_words": 400},
    "research_paper": {"min_words": 600, "max_words": 2000},
    "textbook_chapter": {"min_words": 1000, "max_words": 2000},
    "personal_notes": {"min_words": 200, "max_words": 800},
    "technical_docs": {"min_words": 400, "max_words": 1200},
    "general_article": {"min_words": 800, "max_words": 1600},
    "video_lecture": {"min_words": 600, "max_words": 1400},
    "video_tutorial": {"min_words": 400, "max_words": 1000},
    "video_demo": {"min_words": 400, "max_words": 1000},
}

def get_chunk_params(content_type: str) -> dict[str, int]:
    """Return chunking parameters for a content type."""
    return CHUNK_PARAMS_BY_TYPE.get(
        content_type,
        {"min_words": MIN_CHUNK_WORDS, "max_words": MAX_CHUNK_WORDS},
    )
```

Modify `chunk_section` signature to accept optional `min_words` and `max_words` kwargs, defaulting to the existing constants. The internal logic stays the same but uses the parameters instead of hardcoded values.

**Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_adaptive_chunker.py tests/test_chunker.py -v`
Expected: All PASS (new + existing tests)

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/services/chunker.py
git add apps/api/tests/test_adaptive_chunker.py
git commit -m "feat: adaptive chunking parameters by content type"
```

---

## Phase 3: Adaptive Prompt Templates

### Task 8: Refactor Stage A prompt to be profile-aware

**Files:**
- Modify: `apps/api/src/ankithis_api/llm/prompts/stage_a.py`
- Modify: `apps/api/src/ankithis_api/services/stages/concept_extraction.py`
- Test: `apps/api/tests/test_adaptive_extraction.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_adaptive_extraction.py
from ankithis_api.llm.prompts.stage_a import build_system_prompt, build_user_prompt

def test_system_prompt_adapts_to_research_paper():
    prompt = build_system_prompt(
        content_type="research_paper",
        difficulty="advanced",
        pedagogical_function="data_results",
    )
    assert "findings" in prompt.lower() or "claims" in prompt.lower()
    assert "evidence" in prompt.lower()

def test_system_prompt_adapts_to_lecture_slides():
    prompt = build_system_prompt(
        content_type="lecture_slides",
        difficulty="introductory",
        pedagogical_function="definitions",
    )
    assert "definition" in prompt.lower()

def test_system_prompt_default():
    prompt = build_system_prompt()
    assert "concept" in prompt.lower()  # Generic prompt still works

def test_user_prompt_includes_visual_context():
    prompt = build_user_prompt(
        chunk_text="Some text",
        study_goal="Learn biology",
        visual_context="Diagram shows cell membrane structure",
    )
    assert "cell membrane" in prompt
    assert "diagram" in prompt.lower() or "visual" in prompt.lower()

def test_user_prompt_no_visual_context():
    prompt = build_user_prompt(chunk_text="Some text", study_goal="Learn bio")
    assert "visual" not in prompt.lower()
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_adaptive_extraction.py -v`
Expected: ImportError on `build_system_prompt`

**Step 3: Write the implementation**

Refactor `apps/api/src/ankithis_api/llm/prompts/stage_a.py` — keep existing `SYSTEM` and `USER_TEMPLATE` as the base, and add `build_system_prompt()` and `build_user_prompt()` functions that layer on profile-aware instructions.

The key content-type adaptation blocks (from the design doc Section 2.1) are injected as additional paragraphs into the system prompt. The user prompt gains an optional visual context section.

Update `concept_extraction.py` to call `build_system_prompt()` and `build_user_prompt()` instead of using the raw templates, passing the content profile fields through.

**Step 4: Run tests**

Run: `cd apps/api && python -m pytest tests/test_adaptive_extraction.py tests/ -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/llm/prompts/stage_a.py
git add apps/api/src/ankithis_api/services/stages/concept_extraction.py
git add apps/api/tests/test_adaptive_extraction.py
git commit -m "feat: adaptive Stage A prompts — content-type and difficulty aware"
```

---

### Task 9: Adapt Stages B-E prompts

**Files:**
- Modify: `apps/api/src/ankithis_api/llm/prompts/stage_b.py` through `stage_e.py`
- Modify: `apps/api/src/ankithis_api/services/stages/concept_merge.py`
- Modify: `apps/api/src/ankithis_api/services/stages/card_planning.py`
- Modify: `apps/api/src/ankithis_api/services/stages/card_generation.py`
- Modify: `apps/api/src/ankithis_api/services/stages/critique.py`
- Test: `apps/api/tests/test_adaptive_stages.py`

Follow the same pattern as Task 8 for each stage:

**Stage B (merge):** Add `build_system_prompt(content_type)` that adjusts merge aggressiveness. Lecture slides = aggressive merge instruction. Research papers = light merge. Personal notes = very light.

**Stage C (planning):** Add density modifier by information_density. Override card_ratio per pedagogical_function (definitions → 80% cloze). The `plan_cards()` function already accepts `deck_size` and `card_style` — add `content_profile: dict | None = None` parameter.

**Stage D (generation):** Add difficulty-aware generation rules. Add special_considerations injection (heavy_notation → LaTeX, code_examples → code formatting, etc.). Add the 7 pedagogical principles from the design doc as system prompt rules.

**Stage E (critique):** Add content-type-aware quality bar. Research papers = strict. Personal notes = lenient. Add anti-pattern detection instructions (trivia, verbatim copy, ambiguous cloze, compound questions).

Each stage function gains an optional `content_profile: dict | None = None` parameter. If None, behavior is identical to current (backward compatible).

**Test:** Verify each adapted prompt builder produces different output for different content types.

**Commit:**

```bash
git commit -m "feat: adaptive prompts for Stages B-E — profile-aware generation and critique"
```

---

### Task 10: Enhanced QC anti-pattern detection

**Files:**
- Modify: `apps/api/src/ankithis_api/services/qc.py`
- Test: `apps/api/tests/test_qc_enhanced.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_qc_enhanced.py
from ankithis_api.services.qc import _check_card

def test_trivia_detection():
    card = {"front": "What year was penicillin discovered?", "back": "1928", "card_type": "basic"}
    reason = _check_card(card)
    assert reason is not None
    assert "trivia" in reason

def test_verbatim_detection():
    source = "The mitochondria is the powerhouse of the cell and produces ATP."
    card = {
        "front": "What is the mitochondria?",
        "back": "The mitochondria is the powerhouse of the cell and produces ATP.",
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
```

**Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_qc_enhanced.py -v`
Expected: FAIL — current `_check_card` doesn't detect these patterns

**Step 3: Implement enhanced checks**

Add to `qc.py`:
- `_is_trivia(front)` — regex for "what year", "who discovered", "where was" without conceptual depth
- `_is_verbatim(back, source_text)` — >60% word overlap with source
- `_is_ambiguous_cloze(front)` — cloze deletion is a common word with <3 surrounding context words
- `_is_compound_question(front)` — contains " and " joining two question phrases
- `_lacks_context(front)` — basic card front <8 words with no contextualizing clause

Modify `_check_card()` signature to accept optional `source_text` parameter. Modify `run_qc()` to pass source text through.

**Step 4: Run tests**

Run: `cd apps/api && python -m pytest tests/test_qc_enhanced.py tests/test_chunker.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add apps/api/src/ankithis_api/services/qc.py apps/api/tests/test_qc_enhanced.py
git commit -m "feat: enhanced QC — trivia, verbatim, ambiguous cloze, compound question detection"
```

---

## Phase 4: Pipeline Integration

### Task 11: Wire Stage 0 into the pipeline

**Files:**
- Modify: `apps/api/src/ankithis_api/services/pipeline.py`
- Modify: `apps/api/src/ankithis_api/routers/upload.py` (annotate sections during upload)
- Test: `apps/api/tests/test_pipeline_integration.py`

**Step 1: Write the failing test**

```python
# apps/api/tests/test_pipeline_integration.py
from ankithis_api.services.stages.classification import classify_document, DEFAULT_PROFILE
from ankithis_api.services.section_annotator import annotate_section
from ankithis_api.services.chunker import get_chunk_params

def test_profile_flows_to_chunk_params():
    """Profile content_type should produce valid chunk params."""
    for ct in ["lecture_slides", "research_paper", "personal_notes"]:
        profile = dict(DEFAULT_PROFILE, content_type=ct)
        params = get_chunk_params(profile["content_type"])
        assert "min_words" in params
        assert "max_words" in params
        assert params["min_words"] < params["max_words"]
```

**Step 2-5:** Modify `pipeline.py:run_pipeline()` to:

1. After loading the document, call `classify_document(sections)` to get the profile
2. Persist the ContentProfile to DB
3. Annotate each section with `annotate_section()`
4. Pass profile dict to each stage function via the new `content_profile` parameter

The pipeline function signature doesn't change — it still takes `(document_id, job_id, db)`. The profile is internal state.

Update job status to include a new `CLASSIFYING` stage before `STAGE_A`.

**Commit:**

```bash
git commit -m "feat: wire Stage 0 classification into pipeline — profile flows to all stages"
```

---

## Phase 5: YouTube Pipeline

### Task 12: YouTube metadata and transcript extraction

**Files:**
- Create: `apps/api/src/ankithis_api/services/youtube/metadata.py`
- Create: `apps/api/src/ankithis_api/services/youtube/transcript.py`
- Add `yt-dlp` to `pyproject.toml` dependencies
- Test: `apps/api/tests/test_youtube_metadata.py`

Implement `fetch_metadata(url) -> dict` using yt-dlp to extract title, channel, duration, chapter markers, caption availability. Implement `extract_transcript(video_id) -> list[dict]` to get timestamped transcript segments (manual captions preferred, auto-generated fallback).

---

### Task 13: Visual intelligence assessment

**Files:**
- Create: `apps/api/src/ankithis_api/services/youtube/visual_assessment.py`
- Create: `apps/api/src/ankithis_api/llm/prompts/visual_assess.py`
- Add `VisualAssessmentOutput` to `schemas.py`
- Test: `apps/api/tests/test_visual_assessment.py`

Implement `assess_visuals(video_path, duration) -> dict` that:
1. Samples 6 frames evenly across the video using yt-dlp frame extraction
2. Sends frames to Kimi K2.5 (multimodal) via Bedrock Converse with image content blocks
3. Returns `{visual_density, video_type, recommended_sampling}`
4. Falls back to `{visual_density: "low", recommended_sampling: "skip"}` on failure

---

### Task 14: Scene detection and frame analysis

**Files:**
- Create: `apps/api/src/ankithis_api/services/youtube/frame_sampler.py`
- Create: `apps/api/src/ankithis_api/services/youtube/frame_analyzer.py`
- Test: `apps/api/tests/test_frame_sampler.py`

Implement pixel-diff scene detection (compare consecutive frames, flag transitions above threshold). Implement frame analysis via Kimi K2.5 multimodal — batches of 4-6 frames with surrounding transcript context, extracting only additive visual information.

---

### Task 15: YouTube sectioning and chunk assembly

**Files:**
- Create: `apps/api/src/ankithis_api/services/youtube/sectioner.py`
- Create: `apps/api/src/ankithis_api/services/youtube/assembler.py`
- Test: `apps/api/tests/test_youtube_assembler.py`

Implement transcript sectioning (chapter markers → topic shift detection → LLM fallback). Implement chunk assembly that produces `ParsedSection` objects with `visual_context` populated from frame annotations.

---

### Task 16: YouTube intake router and API endpoint

**Files:**
- Create: `apps/api/src/ankithis_api/routers/youtube.py`
- Modify: `apps/api/src/ankithis_api/app.py` (register router)
- Test: `apps/api/tests/test_youtube_router.py`

New endpoint: `POST /api/youtube` accepting `{url, study_goal, card_style, deck_size}`. Validates URL, fetches metadata, creates Document record with `file_type=youtube`, creates VideoSource record, runs transcript + visual pipeline, creates sections and chunks, returns same `UploadResponse` as file upload.

---

## Phase 6: Frontend — YouTube Support + Adaptive Stages

### Task 17: Upload page — add YouTube URL input

**Files:**
- Modify: `apps/web/src/app/upload/page.tsx`
- Modify: `apps/web/src/lib/api.ts` (add `uploadYouTube()`)
- Modify: `apps/web/src/lib/types.ts` (add YouTube-related types)

Add a toggle or tab on the upload page: "File" | "YouTube URL". When YouTube is selected, show a URL text input instead of the dropzone. On paste, fetch metadata preview (thumbnail, title, duration, channel) via a new `/api/youtube/preview` endpoint. If chapter markers exist, show them as checkboxes. Same configuration options below (study goal, card style, deck size).

---

### Task 18: Processing page — adaptive stage display

**Files:**
- Modify: `apps/web/src/lib/types.ts` (add new stages)
- Modify: `apps/web/src/app/processing/[jobId]/page.tsx`

Add `CLASSIFYING` to `JobStatus` and stage display. For YouTube jobs, show extended stages: "Fetching video" → "Extracting transcript" → "Analyzing visuals" → then standard stages. The `JobStatusResponse` should include a `source_type` field so the frontend knows which stage list to show.

---

## Phase 7: Testing & Polish

### Task 19: Integration test — full document pipeline with classification

End-to-end test: upload a markdown file → verify ContentProfile is created → verify sections are annotated → verify cards are generated with profile-adapted quality.

### Task 20: Integration test — YouTube pipeline

End-to-end test with a short public YouTube video URL → verify metadata, transcript, visual assessment, and card generation.

### Task 21: Alembic migration verification

Run full migration from clean database. Verify all new tables, columns, and enum values are correct.

### Task 22: Update .env.example and README

Add any new environment variables. Document the YouTube feature and adaptive intelligence in README.

---

## Dependency Summary

**New Python packages:**
- `yt-dlp` — YouTube metadata and transcript extraction
- `Pillow` — Frame image processing (likely already available via pdfplumber)

**No new frontend packages needed** — existing Next.js + Tailwind handles the YouTube UI.

## Execution Order

Tasks 1-3 (schema) must come first. Tasks 4-7 (Stage 0) depend on schema. Tasks 8-10 (adaptive prompts) can run in parallel. Task 11 (integration) depends on 4-10. Tasks 12-16 (YouTube) can start after schema (Task 3) and run in parallel with prompt work. Tasks 17-18 (frontend) depend on API endpoints being ready. Tasks 19-22 (testing) come last.

Critical path: **1 → 2 → 3 → 4 → 6 → 11 → 19**
