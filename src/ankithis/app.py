from fastapi import FastAPI

app = FastAPI(
    title="ankithis",
    description="Extract core principles from PDFs and generate Anki cloze flashcard decks",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}
