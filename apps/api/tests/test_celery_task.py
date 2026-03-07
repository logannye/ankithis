"""Tests for Celery task dispatching and regeneration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ankithis_api.worker import celery_app


def test_celery_config():
    """Verify Celery app configuration."""
    assert celery_app.conf.task_time_limit == 600
    assert celery_app.conf.task_soft_time_limit == 540
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.worker_concurrency == 2


def test_generate_task_registered():
    """Verify generate_cards_task is registered."""
    from ankithis_api.tasks.generation import generate_cards_task

    assert generate_cards_task.name == "ankithis.generate_cards"


@patch("ankithis_api.tasks.generation._run_pipeline")
def test_generate_task_calls_pipeline(mock_pipeline):
    """Task calls _run_pipeline with correct UUIDs."""
    import asyncio
    from unittest.mock import AsyncMock

    mock_pipeline.return_value = None
    # Make asyncio.run work with the mock
    mock_pipeline.side_effect = None

    from ankithis_api.tasks.generation import generate_cards_task

    doc_id = "12345678-1234-5678-1234-567812345678"
    job_id = "87654321-4321-8765-4321-876543218765"

    with patch("ankithis_api.tasks.generation.asyncio") as mock_asyncio:
        mock_asyncio.run = MagicMock()
        result = generate_cards_task(doc_id, job_id)

    assert result["document_id"] == doc_id
    assert result["job_id"] == job_id
    assert result["status"] == "completed"
    mock_asyncio.run.assert_called_once()
