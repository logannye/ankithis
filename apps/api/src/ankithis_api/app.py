from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ankithis_api.config import settings
from ankithis_api.routers import (
    cards,
    export,
    generate,
    health,
    jobs,
    regenerate,
    review,
    sections,
    upload,
)

app = FastAPI(
    title="AnkiThis",
    description="Convert documents into high-quality Anki flashcard decks",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(jobs.router)
app.include_router(export.router)
app.include_router(review.router)
app.include_router(cards.router)
app.include_router(sections.router)
app.include_router(regenerate.router)
