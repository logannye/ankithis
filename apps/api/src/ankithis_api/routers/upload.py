"""Upload endpoint: accepts a file + options, parses, chunks, stores in DB."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.auth import get_current_user
from ankithis_api.config import settings
from ankithis_api.db import get_db
from ankithis_api.models.document import Chunk, Document, DocumentOptions, Section
from ankithis_api.models.enums import CardStyle, DeckSize, DocumentStatus, FileType
from ankithis_api.models.user import User
from ankithis_api.rate_limit import check_rate_limit
from ankithis_api.schemas.upload import UploadResponse
from ankithis_api.services.chunker import chunk_section
from ankithis_api.services.parser import parse_document
from ankithis_api.services.storage import save_upload

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".txt": FileType.TXT,
    ".md": FileType.MD,
}


@router.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    study_goal: str | None = Form(None),
    card_style: CardStyle = Form(CardStyle.CLOZE_HEAVY),
    deck_size: DeckSize = Form(DeckSize.MEDIUM),
    scope: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_rate_limit(str(user.id), "upload", settings.rate_limit_uploads)
    # Validate file type
    ext = Path(file.filename or "").suffix.lower()
    file_type = ALLOWED_EXTENSIONS.get(ext)
    if not file_type:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"File too large. Maximum: {max_mb}MB")

    if len(content) == 0:
        raise HTTPException(status_code=422, detail="File is empty")

    # Store the raw file
    storage_path = save_upload(content, file.filename or "upload")

    # Parse the document
    try:
        parse_result = parse_document(storage_path, file_type)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse document: {e}")

    # Validate page count for PDFs
    if parse_result.page_count and parse_result.page_count > settings.max_pages:
        raise HTTPException(
            status_code=413,
            detail=f"Document has {parse_result.page_count} pages. Maximum: {settings.max_pages}",
        )

    # Create Document record
    doc = Document(
        id=uuid.uuid4(),
        user_id=user.id,
        filename=file.filename or "upload",
        file_type=file_type,
        file_size=len(content),
        storage_path=storage_path,
        status=DocumentStatus.PARSED,
        title=_extract_title(parse_result.sections, file.filename),
        page_count=parse_result.page_count,
        word_count=parse_result.word_count,
    )
    db.add(doc)

    # Create DocumentOptions
    options = DocumentOptions(
        document_id=doc.id,
        study_goal=study_goal,
        card_style=card_style,
        deck_size=deck_size,
        scope=scope,
    )
    db.add(options)

    # Create Sections and Chunks
    total_chunks = 0
    for pos, parsed_section in enumerate(parse_result.sections):
        section = Section(
            id=uuid.uuid4(),
            document_id=doc.id,
            title=parsed_section.title,
            position=pos,
            level=parsed_section.level,
            word_count=parsed_section.word_count,
        )
        db.add(section)

        chunks = chunk_section(parsed_section.paragraphs, start_position=0)
        for chunk in chunks:
            db.add(
                Chunk(
                    section_id=section.id,
                    text=chunk.text,
                    position=chunk.position,
                    word_count=chunk.word_count,
                )
            )
            total_chunks += 1

    await db.commit()

    return UploadResponse(
        document_id=str(doc.id),
        filename=doc.filename,
        file_type=doc.file_type.value,
        section_count=len(parse_result.sections),
        chunk_count=total_chunks,
        word_count=parse_result.word_count,
    )


def _extract_title(sections, filename: str | None) -> str:
    """Try to get a title from the first section heading, fall back to filename."""
    for s in sections:
        if s.title:
            return s.title
    if filename:
        return Path(filename).stem
    return "Untitled"
