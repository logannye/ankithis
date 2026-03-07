from pydantic import BaseModel


class SectionSummary(BaseModel):
    id: str
    title: str | None
    position: int
    level: int
    word_count: int
    chunk_count: int
    excluded: bool


class DocumentSummary(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    title: str | None
    word_count: int | None
    section_count: int
    chunk_count: int
    card_count: int


class DocumentDetail(DocumentSummary):
    sections: list[SectionSummary]
    study_goal: str | None = None
    card_style: str | None = None
    deck_size: str | None = None
    scope: str | None = None
