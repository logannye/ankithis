"""Celery application configuration."""

from celery import Celery

from ankithis_api.config import settings

celery_app = Celery(
    "ankithis",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minute hard limit
    task_soft_time_limit=540,  # 9 minute soft limit
    task_acks_late=True,  # Ack after completion (crash safety)
    worker_prefetch_multiplier=1,  # LLM-bound, don't prefetch
    worker_concurrency=2,
)

# Auto-discover tasks — looks for 'tasks' submodule in each listed package
celery_app.autodiscover_tasks(["ankithis_api"])
