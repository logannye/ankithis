import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ankithis_api.models.base import Base, TimestampMixin, UUIDMixin
from ankithis_api.models.enums import JobStatus


class GenerationJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "generation_jobs"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, native_enum=False, length=32), default=JobStatus.PENDING, nullable=False
    )
    current_stage: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    total_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    suppressed_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Concept(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "concepts"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5, nullable=False)  # 1-10
    merged: Mapped[bool] = mapped_column(default=False, nullable=False)


class CardPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "card_plans"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    card_type: Mapped[str] = mapped_column(String(32), nullable=False)  # cloze or basic
    direction: Mapped[str] = mapped_column(String(256), nullable=False)  # what to test
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    bloom_level: Mapped[str] = mapped_column(
        String(32), default="understand", server_default="understand", nullable=False
    )  # Bloom's taxonomy: remember, understand, apply, analyze, evaluate, create
