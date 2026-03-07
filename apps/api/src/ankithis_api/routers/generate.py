"""Generate endpoint: kick off the LLM pipeline for a document."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.auth import get_current_user
from ankithis_api.config import settings
from ankithis_api.db import get_db
from ankithis_api.models.document import Document
from ankithis_api.models.enums import DocumentStatus, JobStatus
from ankithis_api.models.generation import GenerationJob
from ankithis_api.models.user import User
from ankithis_api.rate_limit import check_rate_limit
from ankithis_api.schemas.generation import GenerateResponse
from ankithis_api.tasks.generation import generate_cards_task

router = APIRouter()


@router.post("/api/documents/{document_id}/generate", response_model=GenerateResponse)
async def generate_cards(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_rate_limit(str(user.id), "generation", settings.rate_limit_generations)

    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status not in (DocumentStatus.PARSED, DocumentStatus.COMPLETED):
        raise HTTPException(
            status_code=409,
            detail=f"Document is in '{doc.status.value}' state. Must be 'parsed' or 'completed' to generate.",
        )

    job = GenerationJob(
        id=uuid.uuid4(),
        document_id=document_id,
        status=JobStatus.PENDING,
    )
    doc.status = DocumentStatus.GENERATING
    db.add(job)
    await db.commit()

    generate_cards_task.delay(str(document_id), str(job.id))

    return GenerateResponse(job_id=str(job.id), status=job.status.value)
