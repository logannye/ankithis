from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ankithis_api.config import settings
from ankithis_api.middleware import add_middleware, setup_logging
from ankithis_api.routers import (
    auth,
    cards,
    export,
    generate,
    health,
    jobs,
    regenerate,
    review,
    sections,
    upload,
    youtube,
)

setup_logging()

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

add_middleware(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(jobs.router)
app.include_router(export.router)
app.include_router(review.router)
app.include_router(cards.router)
app.include_router(sections.router)
app.include_router(regenerate.router)
app.include_router(youtube.router)
