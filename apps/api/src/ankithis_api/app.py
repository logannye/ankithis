from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ankithis_api.config import settings
from ankithis_api.routers import health, upload

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
