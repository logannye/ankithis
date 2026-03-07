"""Celery task for running the card generation pipeline."""

from __future__ import annotations

import asyncio
import logging
import uuid

from ankithis_api.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="ankithis.generate_cards", max_retries=0)
def generate_cards_task(self, document_id: str, job_id: str) -> dict:
    """Run the full generation pipeline as a Celery task.

    The pipeline is async (SQLAlchemy async), so we run it in an event loop.
    """
    doc_uuid = uuid.UUID(document_id)
    job_uuid = uuid.UUID(job_id)

    logger.info(f"Starting generation task for document={document_id} job={job_id}")

    try:
        asyncio.run(_run_pipeline(doc_uuid, job_uuid))
    except Exception:
        logger.exception(f"Generation task failed for document={document_id}")
        # Error handling is done inside run_pipeline (marks job as FAILED)
        # Re-raise so Celery marks the task as failed too
        raise

    return {"document_id": document_id, "job_id": job_id, "status": "completed"}


async def _run_pipeline(document_id: uuid.UUID, job_id: uuid.UUID) -> None:
    """Async wrapper that creates a DB session and runs the pipeline."""
    from ankithis_api.db import async_session
    from ankithis_api.services.pipeline import run_pipeline

    async with async_session() as db:
        await run_pipeline(document_id, job_id, db)
