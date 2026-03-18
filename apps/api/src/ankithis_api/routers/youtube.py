"""YouTube intake endpoint — process a YouTube URL into document records."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.auth import get_current_user
from ankithis_api.db import get_db
from ankithis_api.models.document import Chunk, Document, DocumentOptions, Section
from ankithis_api.models.enums import (
    CardStyle,
    DeckSize,
    DocumentStatus,
    FileType,
)
from ankithis_api.models.video_source import VideoSource
from ankithis_api.services.youtube.metadata import extract_video_id, fetch_metadata
from ankithis_api.services.youtube.transcript import (
    extract_transcript,
    transcript_to_text,
    transcript_word_count,
)
from ankithis_api.services.youtube.sectioner import (
    section_by_chapters,
    section_by_topic_shifts,
)
from ankithis_api.services.youtube.assembler import assemble_chunks
from ankithis_api.services.chunker import chunk_section, get_chunk_params
from ankithis_api.services.section_annotator import annotate_section

logger = logging.getLogger(__name__)

router = APIRouter()

# Duration limits (seconds)
MAX_DURATION = 3 * 60 * 60  # 3 hours
WARN_DURATION = 90 * 60  # 90 minutes


class YouTubeRequest(BaseModel):
    url: str
    study_goal: str = ""
    card_style: CardStyle = CardStyle.CLOZE_HEAVY
    deck_size: DeckSize = DeckSize.MEDIUM
    scope: str = ""

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        if not extract_video_id(v):
            raise ValueError("Invalid YouTube URL")
        return v


class YouTubePreviewResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    duration_seconds: int
    thumbnail_url: str
    has_chapters: bool
    chapters: list[dict]


class YouTubeUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    section_count: int
    chunk_count: int
    word_count: int


@router.post("/api/youtube/preview", response_model=YouTubePreviewResponse)
async def preview_youtube(
    req: YouTubeRequest,
    user=Depends(get_current_user),
):
    """Fetch YouTube video metadata for preview before processing."""
    try:
        meta = fetch_metadata(req.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video: {exc}")

    if meta["duration_seconds"] > MAX_DURATION:
        raise HTTPException(
            status_code=400,
            detail=f"Video is too long ({meta['duration_seconds']}s). Max is {MAX_DURATION}s.",
        )

    return YouTubePreviewResponse(
        video_id=meta["video_id"],
        title=meta["title"],
        channel=meta["channel"],
        duration_seconds=meta["duration_seconds"],
        thumbnail_url=meta["thumbnail_url"],
        has_chapters=bool(meta["chapter_markers"]),
        chapters=meta["chapter_markers"],
    )


@router.post("/api/youtube", response_model=YouTubeUploadResponse)
async def upload_youtube(
    req: YouTubeRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Process a YouTube URL: extract transcript, create document records."""
    # Fetch metadata
    try:
        meta = fetch_metadata(req.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video: {exc}")

    if meta["duration_seconds"] > MAX_DURATION:
        raise HTTPException(status_code=400, detail="Video exceeds maximum duration")

    # Extract transcript
    try:
        segments = extract_transcript(req.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not segments:
        raise HTTPException(
            status_code=400, detail="No transcript available for this video"
        )

    word_count = transcript_word_count(segments)

    # Section the transcript
    if meta["chapter_markers"]:
        sections_data = section_by_chapters(segments, meta["chapter_markers"])
    else:
        sections_data = section_by_topic_shifts(segments)

    if not sections_data:
        # Fallback: treat entire transcript as one section
        full_text = transcript_to_text(segments)
        sections_data = [
            {
                "title": meta["title"],
                "start_time": 0,
                "end_time": meta["duration_seconds"],
                "text": full_text,
            }
        ]

    # Assemble into ParsedSection format
    assembled = assemble_chunks(sections_data)

    # Create Document record
    document = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        filename=f"{meta['title']}.youtube",
        file_type=FileType.YOUTUBE,
        file_size=0,  # No file on disk
        storage_path="",
        status=DocumentStatus.PARSED,
        title=meta["title"],
        page_count=0,
        word_count=word_count,
    )
    db.add(document)
    await db.flush()

    # Create DocumentOptions
    options = DocumentOptions(
        document_id=document.id,
        study_goal=req.study_goal or None,
        card_style=req.card_style,
        deck_size=req.deck_size,
        scope=req.scope or None,
    )
    db.add(options)

    # Create VideoSource record
    video_source = VideoSource(
        document_id=document.id,
        youtube_url=req.url,
        video_id=meta["video_id"],
        title=meta["title"],
        channel=meta["channel"],
        duration_seconds=meta["duration_seconds"],
        has_manual_captions=meta["has_manual_captions"],
        chapter_markers=meta["chapter_markers"],
    )
    db.add(video_source)

    # Create Sections and Chunks
    total_chunks = 0
    chunk_params = get_chunk_params("video_lecture")

    for pos, (parsed_section, visual_contexts) in enumerate(assembled):
        section = Section(
            id=uuid.uuid4(),
            document_id=document.id,
            title=parsed_section.title,
            position=pos,
            level=parsed_section.level,
            word_count=parsed_section.word_count,
            excluded=False,
        )
        # Annotate pedagogical function
        first_para = parsed_section.paragraphs[0] if parsed_section.paragraphs else ""
        section.pedagogical_function = annotate_section(section.title, first_para)
        db.add(section)
        await db.flush()

        # Chunk the section text
        chunks = chunk_section(
            parsed_section.paragraphs,
            start_position=total_chunks,
            min_words=chunk_params["min_words"],
            max_words=chunk_params["max_words"],
        )

        for chunk in chunks:
            # Attach visual context if available
            visual_ctx = None
            if visual_contexts:
                visual_ctx = visual_contexts[0]  # One visual context per section

            db_chunk = Chunk(
                section_id=section.id,
                text=chunk.text,
                position=chunk.position,
                word_count=chunk.word_count,
                visual_context=visual_ctx,
            )
            db.add(db_chunk)
            total_chunks += 1

    await db.commit()

    return YouTubeUploadResponse(
        document_id=str(document.id),
        filename=document.filename,
        file_type=FileType.YOUTUBE.value,
        section_count=len(assembled),
        chunk_count=total_chunks,
        word_count=word_count,
    )
