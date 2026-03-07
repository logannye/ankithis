"""Job status endpoint for polling generation progress."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.auth import get_current_user
from ankithis_api.db import get_db
from ankithis_api.models.document import Document
from ankithis_api.models.generation import GenerationJob
from ankithis_api.models.user import User
from ankithis_api.schemas.generation import JobStatusResponse

router = APIRouter()


@router.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify ownership through document
    doc_result = await db.execute(
        select(Document).where(Document.id == job.document_id, Document.user_id == user.id)
    )
    if not doc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=str(job.id),
        document_id=str(job.document_id),
        status=job.status.value,
        current_stage=job.current_stage,
        error_message=job.error_message,
        total_cards=job.total_cards,
        suppressed_cards=job.suppressed_cards,
    )
