import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ankithis_api.models.base import Base, TimestampMixin, UUIDMixin
from ankithis_api.models.enums import CardType, CritiqueVerdict


class Card(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cards"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="SET NULL")
    )
    card_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("card_plans.id", ondelete="SET NULL")
    )
    card_type: Mapped[CardType] = mapped_column(nullable=False)
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str | None] = mapped_column(String(1024))  # comma-separated
    critique_verdict: Mapped[CritiqueVerdict | None] = mapped_column()
    suppressed: Mapped[bool] = mapped_column(default=False, nullable=False)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
