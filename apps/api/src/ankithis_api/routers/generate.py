"""Generate endpoint: kick off the LLM pipeline for a document."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.db import get_db
from ankithis_api.models.document import Document
from ankithis_api.models.enums import DocumentStatus, JobStatus
from ankithis_api.models.generation import GenerationJob
from ankithis_api.schemas.generation import GenerateResponse
from ankithis_api.services.pipeline import run_pipeline

router = APIRouter()


async def _run_pipeline_bg(document_id: uuid.UUID, job_id: uuid.UUID) -> None:
    """Background task wrapper that creates its own DB session."""
    from ankithis_api.db import async_session

    async with async_session() as db:
        await run_pipeline(document_id, job_id, db)


@router.post("/api/documents/{document_id}/generate", response_model=GenerateResponse)
async def generate_cards(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Verify document exists and is parsed
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status not in (DocumentStatus.PARSED, DocumentStatus.COMPLETED):
        raise HTTPException(
            status_code=409,
            detail=f"Document is in '{doc.status.value}' state. Must be 'parsed' to generate.",
        )

    # Create job
    job = GenerationJob(
        id=uuid.uuid4(),
        document_id=document_id,
        status=JobStatus.PENDING,
    )
    doc.status = DocumentStatus.GENERATING
    db.add(job)
    await db.commit()

    # Run pipeline in background
    background_tasks.add_task(_run_pipeline_bg, document_id, job.id)

    return GenerateResponse(job_id=str(job.id), status=job.status.value)
