from pydantic import BaseModel


class GenerateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    document_id: str
    status: str
    current_stage: str | None
    error_message: str | None
    total_cards: int
    suppressed_cards: int
