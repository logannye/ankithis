"""Regenerate endpoint: re-run the pipeline reusing parsed content."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.db import get_db
from ankithis_api.models.card import Card
from ankithis_api.models.document import Document
from ankithis_api.models.enums import DocumentStatus, JobStatus
from ankithis_api.models.generation import CardPlan, Concept, GenerationJob
from ankithis_api.schemas.generation import GenerateResponse
from ankithis_api.tasks.generation import generate_cards_task

router = APIRouter()


@router.post("/api/documents/{document_id}/regenerate", response_model=GenerateResponse)
async def regenerate_cards(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Re-run the generation pipeline for a document.

    Reuses existing sections and chunks (parsed content).
    Soft-deletes old cards, concepts, and card plans.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status not in (DocumentStatus.COMPLETED, DocumentStatus.FAILED):
        raise HTTPException(
            status_code=409,
            detail=f"Document is in '{doc.status.value}' state. Must be 'completed' or 'failed' to regenerate.",
        )

    # Clean up old generation data (keep sections/chunks)
    await db.execute(delete(Card).where(Card.document_id == document_id))
    await db.execute(delete(CardPlan).where(CardPlan.document_id == document_id))
    await db.execute(delete(Concept).where(Concept.document_id == document_id))

    # Create new job
    job = GenerationJob(
        id=uuid.uuid4(),
        document_id=document_id,
        status=JobStatus.PENDING,
    )
    doc.status = DocumentStatus.GENERATING
    db.add(job)
    await db.commit()

    # Dispatch to Celery worker
    generate_cards_task.delay(str(document_id), str(job.id))

    return GenerateResponse(job_id=str(job.id), status=job.status.value)
