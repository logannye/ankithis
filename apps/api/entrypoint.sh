#!/bin/sh
set -e

if [ "$SERVICE_MODE" = "worker" ]; then
    exec celery -A ankithis_api.worker:celery_app worker --loglevel=info --concurrency=2 --include=ankithis_api.tasks.generation
else
    exec uvicorn ankithis_api.app:app --host 0.0.0.0 --port 8000 --workers 2
fi
