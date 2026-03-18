# AnkiThis — Adaptive Intelligence Engine Design

**Date:** 2026-03-18
**Status:** Approved
**Approach:** Multi-Resolution Intelligence (Approach C)

---

## Problem Statement

AnkiThis currently runs the same pipeline on every input: fixed 800-1600 word chunks, uniform extraction prompts, one-size-fits-all card generation. This produces acceptable cards for well-structured textbook content but degrades on lecture slides (too sparse), research papers (too dense), personal notes (over-extracts), and technical docs (misses the right card patterns). There is also no support for video content.

The Adaptive Intelligence Engine adds a pre-pipeline classification layer, content-aware chunking, per-stage prompt adaptation, a YouTube intake pipeline, and a pedagogical quality engine — all without replacing the existing 6-stage architecture.

---

## Design Principles

1. **Classify first, then adapt** — every input gets profiled before any card generation begins
2. **Converge to the same interface** — YouTube and documents both produce ContentProfile + Chunks; Stages A-F don't know or care about the source
3. **Degrade gracefully** — if any adaptive component fails, the pipeline falls back to current behavior
4. **Respect the source's emphasis** — more coverage for heavily-emphasized material, less for passing mentions
5. **Test understanding, not recognition** — cards require reconstruction of knowledge, not dictionary lookup

---

## Section 1: Stage 0 — Content Intelligence Engine

### 1.1 Input Routing

| Input | Route | Pre-processing |
|-------|-------|----------------|
| PDF/DOCX/MD/TXT | Document path — parse → section → chunk → profile | Existing parsers (enhanced) |
| YouTube URL | Video path — metadata → transcript → frame sampling → profile | New pipeline (Section 3) |

URL regex for YouTube, MIME type for files.

### 1.2 Document-Level Classification (1 LLM call)

Samples first ~2000 words + all section headings + last ~500 words. Returns:

```
ContentProfile {
  content_type: enum        # lecture_slides | research_paper | textbook_chapter |
                            # personal_notes | technical_docs | general_article |
                            # video_lecture | video_tutorial | video_demo
  domain: string            # "organic chemistry", "machine learning", "US history"
  difficulty: enum          # introductory | intermediate | advanced | expert
  information_density: enum # sparse | moderate | dense | very_dense
  structure_quality: enum   # well_structured | semi_structured | unstructured
  primary_knowledge_type: enum  # factual | conceptual | procedural | mixed
  recommended_card_ratio: {
    cloze: float
    basic_qa: float
  }
  special_considerations: string[]  # e.g., ["heavy_notation", "code_examples",
                                    #  "visual_diagrams_referenced", "foreign_language_terms"]
}
```

### 1.3 Section-Level Annotation (heuristic, no LLM)

Each section annotated with pedagogical function from heading text + first paragraph keywords:

| Function | Signals | Card Strategy |
|----------|---------|---------------|
| `definitions` | "Definition:", "is defined as", glossary-style | Heavy cloze (terms → blanks) |
| `theory` | "mechanism", "principle", "model", abstract language | Basic Q&A (why/how questions) |
| `methodology` | "protocol", "steps", "procedure", numbered lists | Procedural cards (step sequencing) |
| `examples` | "Example:", "case study", "consider the following" | Application cards (given X, what happens?) |
| `data_results` | Tables, numbers, "Figure X shows", "p < 0.05" | Interpretation cards (what does this data mean?) |
| `summary` | "In summary", "Key takeaways", end of chapter | Skip or very light — redundant |
| `code` | Code blocks, `function`, `class`, syntax patterns | Cloze on syntax, Q&A on behavior |
| `enumeration` | Bullet lists of properties, characteristics, types | One card per item or grouped cloze |

If heuristic confidence is low, section tagged `unknown` and Stage A classifies inline.

### 1.4 Adaptive Chunking

| Content Type | Chunk Strategy |
|-------------|----------------|
| Lecture slides | 1 slide = 1 chunk (even if only 50 words) |
| Research paper | Section-aligned. Abstract = 1 chunk. Methods = 1-2. No cross-section splits. |
| Textbook | Subsection-aligned, 1000-2000 words. Respect heading hierarchy. |
| Personal notes | Paragraph-group chunks, 400-800 words (already condensed). |
| Technical docs | Function/topic-aligned. Each API endpoint or concept block = 1 chunk. |
| General article | Current strategy (800-1600 words, paragraph boundaries). |

Key principle: chunk boundaries align with semantic boundaries, not word counts.

---

## Section 2: Adaptive Pipeline — Per-Stage Behavior

### 2.1 Stage A: Concept Extraction

Prompt is now a template with slots filled by ContentProfile.

**Adaptation by content type:**

| Content Type | What Counts as a Concept |
|-------------|-------------------------|
| Lecture slides | The complete idea each bullet abbreviates + cross-slide relationships |
| Research paper | Findings, methods rationale, limitations |
| Textbook | Definitions, causal mechanisms, procedures |
| Personal notes | The note itself + implicit prerequisites |
| Technical docs | API behaviors, configuration effects, trade-offs |
| General article | Claims and their evidence |

**Adaptation by difficulty:**

| Difficulty | Behavior |
|-----------|----------|
| Introductory | More concepts, simpler phrasing. Definitions aggressively extracted. |
| Intermediate | Balance definitions and relationships. "How X relates to Y." |
| Advanced | Fewer but deeper. Nuances, exceptions, edge cases. |
| Expert | Only novel findings, methodological innovations, points of disagreement. |

**Adaptation by section function:** Section annotation directly modifies extraction prompt. `definitions` section gets definition-specific instructions; `methodology` gets procedure-specific instructions.

### 2.2 Stage B: Concept Merge

| Content Type | Merge Aggressiveness |
|-------------|---------------------|
| Lecture slides | Aggressive — slides repeat for emphasis |
| Research paper | Light — different framings of same finding are pedagogically valuable |
| Textbook | Moderate — merge definitions, keep distinct applications |
| Personal notes | Very light — assume user's curation is intentional |

### 2.3 Stage C: Card Planning

Base density from user's deck size × content density modifier:

| Information Density | Modifier |
|-------------------|----------|
| `sparse` | 1.5x |
| `moderate` | 1.0x |
| `dense` | 0.8x |
| `very_dense` | 0.6x |

Card type ratio from ContentProfile, adjusted per section:
- `definitions` → 80% cloze
- `theory` → 70% basic Q&A
- `methodology` → 50/50
- `code` → 90% cloze

User's card style preference acts as a bias, not an absolute.

### 2.4 Stage D: Card Generation

Prompts adapt by difficulty level:

| Difficulty | Rules |
|-----------|-------|
| Introductory | Simple language. Define jargon in answer. One concept per card. Single-term cloze. |
| Intermediate | Assume foundational vocabulary. Can reference related concepts. 2-3 word cloze phrases. |
| Advanced | Assume domain fluency. Test nuance, distinctions, failure conditions. |
| Expert | Frontier testing: methodology critiques, assumptions, cross-field implications. |

Special considerations inject additional rules: `heavy_notation` → preserve LaTeX; `code_examples` → inline code formatting; `foreign_language_terms` → bidirectional cards; `visual_diagrams_referenced` → describe visual in card.

### 2.5 Stage E: Critique

| Content Type | Quality Bar |
|-------------|------------|
| Research paper | Strict — suppress oversimplifications, require caveats |
| Lecture slides | Moderate — accept gist-level cards |
| Personal notes | Lenient — respect user's framing |
| Technical docs | Strict on accuracy — wrong parameters are dangerous |

### 2.6 Stage F: Dedup

Unchanged — semantic similarity is content-agnostic.

---

## Section 3: YouTube Pipeline

### 3.1 Architecture

YouTube pipeline is an alternative intake that produces the same ContentProfile + Chunks as documents. Stages A-F run identically regardless of source.

### 3.2 Processing Steps

**Step 1: Metadata Fetch** (no LLM)
- `yt-dlp` or YouTube Data API
- Title, description, channel, duration, category, chapter markers, language

**Step 2: Transcript Extraction** (no LLM)
- Priority: manual captions → auto-generated captions → Whisper fallback
- Output: timestamped segments

**Step 3: Visual Intelligence Assessment** (1 LLM call, 6 frames)
- Sample 6 frames evenly across video
- Send to Kimi K2.5 (multimodal)
- Returns: `visual_density` (low/medium/high), `video_type`, `recommended_sampling`

**Step 4: Scene-Based Frame Sampling** (conditional)
- If `skip`: done, transcript only
- If `transitions_only`: pixel-diff scene detection, keep first stable frame per transition
- If `dense`: transition frames + 1 frame per 30 seconds within each scene

**Step 5: Frame Analysis** (conditional LLM, batches of 4-6)
- Prompt: extract visual information NOT already in transcript
- Returns per frame: `visual_content`, `content_type`, `additive_value`
- Discard frames with `additive_value: none`

**Step 6: Transcript Sectioning**
- Priority: YouTube chapter markers → topic shift detection (pauses, transition phrases, scene changes) → LLM fallback

**Step 7: Chunk Assembly**
- Each section → chunks with `text` + `visual_context` (nullable)
- Visual context from frame annotations within timestamp range
- Stage A prompt includes both transcript and visual context

**Step 8: Content Profile Generation**
- Same schema as documents, `content_type` set to `video_lecture` / `video_tutorial` / `video_demo`

### 3.3 Duration Guardrails

| Duration | Strategy |
|----------|----------|
| < 5 min | Process entirely |
| 5-30 min | Standard pipeline, 1-3 sections |
| 30-90 min | Full pipeline, 3-10 sections |
| 90+ min | Warn user. Allow section selection if chapter markers exist. |
| > 3 hours | Reject or require time range |

### 3.4 User Experience

Upload page gains a URL field alongside file dropzone. When YouTube URL detected:
1. Instant feedback: thumbnail, title, duration, channel
2. Chapter markers shown as selectable checkboxes (if available)
3. Same configuration options (study goal, card style, deck size)
4. Processing page shows adapted stages: Fetching video → Extracting transcript → Analyzing visuals → then standard pipeline stages

---

## Section 4: Pedagogical Engine

### 4.1 The Seven Card Quality Principles

**Principle 1: Test Understanding, Not Recognition**
- Every Q&A card must require explain, compare, apply, or predict — never bare "What is X?"
- Definitions belong in cloze cards

**Principle 2: One Atomic Idea Per Card**
- Each card tests exactly one thing
- Stage E suppresses compound cards, rewrites as split atomic units

**Principle 3: Cloze Deletions Must Have Exactly One Valid Answer**
- Surrounding context must uniquely determine the answer
- Stage E checks: could a knowledgeable student fill in a different correct answer?

**Principle 4: Bidirectional Cards Where Appropriate**
- Key terminology: term→definition AND definition→term
- Only for terms the learner is expected to produce, not just recognize

**Principle 5: Difficulty Should Scaffold**
- Priority 1-3: foundational definitions and core facts
- Priority 4-6: relationships, comparisons, applications
- Priority 7-10: edge cases, exceptions, synthesis
- Exporter sorts by priority ascending

**Principle 6: Context Over Isolation**
- Every card includes enough context for "why this matters"
- Prefer "In the context of X, what/why/how..." over bare questions

**Principle 7: Respect the Source's Emphasis**
- Importance scored by coverage and emphasis in source material
- Multi-section appearance = 8-10 importance
- Passing mention = 1-3 importance

### 4.2 Content-Type Specific Rules

**Research Papers:** Central finding card (always). Limitation awareness cards. "So what" implication cards. No statistical trivia unless study goal targets methodology.

**Lecture Slides:** Slide titles as potential card fronts. Bullet enumerations as grouped cards. Infer cross-slide connections.

**Technical Docs:** "When to use" cards. "Gotcha" cards for pitfalls. Parameter behavior cards. Skip rarely-used options.

**Personal Notes:** Respect user's curation. Focus on filling gaps and prerequisites. Keep user's language.

**Video Content:** Reference what was shown, not just said. "What would happen if" cards from demonstrations. Describe visuals in card text for standalone use.

### 4.3 Anti-Pattern Detection (QC)

| Anti-Pattern | Detection | Action |
|-------------|-----------|--------|
| Trivia | "what year", "who discovered" without conceptual depth | Suppress |
| Verbatim copy | >60% word overlap with source chunk | Rewrite flag |
| Ambiguous cloze | Common word deletion with <3 context words | Suppress |
| Compound question | "and" joining two independent questions | Split flag |
| Missing context | Card front <8 words, no contextualizing clause | Rewrite flag |
| Orphan jargon | Term used but not defined in any deck card | Add definition card or define in answer |

---

## Section 5: End-to-End Data Flow

### 5.1 LLM Call Budget

**Document (20 pages, ~8000 words, 6 chunks):**

| Stage | Calls |
|-------|-------|
| Stage 0: Classify | 1 |
| Stage A: Extract | 6 |
| Stage B: Merge | 1-2 |
| Stage C: Plan | 1 |
| Stage D: Generate | 3-5 |
| Stage E: Critique | 2-4 |
| Stage F: Dedup | 1 |
| **Total** | **~15-19** |

**YouTube (45 min, medium visual density):**

| Stage | Calls |
|-------|-------|
| Visual assessment | 1 |
| Frame analysis | 3-5 |
| Transcript sectioning | 0-1 |
| Stage 0 + A-F + QC | ~15-19 |
| **Total** | **~20-26** |

### 5.2 Database Schema Changes

**New: `content_profiles`**
- id, document_id (FK), content_type, domain, difficulty, information_density, structure_quality, primary_knowledge_type, recommended_cloze_ratio, recommended_qa_ratio, special_considerations (JSON), created_at

**New: `video_sources`**
- id, document_id (FK), youtube_url, video_id, title, channel, duration_seconds, has_manual_captions, visual_density, video_type, chapter_markers (JSON), created_at

**Modified: `sections`** — add `pedagogical_function` enum

**Modified: `chunks`** — add `visual_context` text (nullable)

**Modified: `documents`** — add `youtube` to `file_type` enum

### 5.3 Error Handling & Graceful Degradation

| Component | Failure | Fallback |
|-----------|---------|----------|
| Visual assessment | LLM fails | Assume low density, transcript only |
| Frame sampling | Scene detection fails | 1 frame per 60s uniform |
| Frame analysis | LLM fails on batch | Skip batch, proceed with transcript |
| Transcript extraction | No captions, Whisper fails | Reject with clear error |
| Content classification | Malformed profile | Defaults: general_article, moderate, intermediate |
| Section annotation | Low confidence | Tag unknown, Stage A classifies inline |
| Chapter markers | None exist | Topic shift detection → LLM sectioning |

Principle: if every new component fails, pipeline works exactly as it does today.

### 5.4 Frontend Stage Display

**Document:** ① Analyzing content → ② Extracting concepts → ③ Planning cards → ④ Writing cards → ⑤ Quality review → ⑥ Finalizing deck

**YouTube:** ① Fetching video → ② Extracting transcript → ③ Analyzing visuals → ④ Analyzing content → ⑤ Extracting concepts → ⑥ Planning cards → ⑦ Writing cards → ⑧ Quality review → ⑨ Finalizing deck
