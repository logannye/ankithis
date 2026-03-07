from pydantic import BaseModel, Field

from ankithis_api.models.enums import CardStyle, DeckSize


class UploadOptions(BaseModel):
    study_goal: str | None = None
    card_style: CardStyle = CardStyle.CLOZE_HEAVY
    deck_size: DeckSize = DeckSize.MEDIUM
    scope: str | None = None


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    section_count: int
    chunk_count: int
    word_count: int
