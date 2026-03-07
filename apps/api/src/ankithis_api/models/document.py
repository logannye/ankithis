import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ankithis_api.models.base import Base, TimestampMixin, UUIDMixin
from ankithis_api.models.enums import CardStyle, DeckSize, DocumentStatus, FileType


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, native_enum=False, length=16), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=32), default=DocumentStatus.UPLOADED, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(512))
    page_count: Mapped[int | None] = mapped_column(Integer)
    word_count: Mapped[int | None] = mapped_column(Integer)

    options: Mapped["DocumentOptions | None"] = relationship(
        back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    sections: Mapped[list["Section"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="Section.position"
    )


class DocumentOptions(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_options"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    study_goal: Mapped[str | None] = mapped_column(Text)
    card_style: Mapped[CardStyle] = mapped_column(Enum(CardStyle, native_enum=False, length=32), default=CardStyle.CLOZE_HEAVY, nullable=False)
    deck_size: Mapped[DeckSize] = mapped_column(Enum(DeckSize, native_enum=False, length=32), default=DeckSize.MEDIUM, nullable=False)
    scope: Mapped[str | None] = mapped_column(Text)  # "focus on chapters 3-5"

    document: Mapped["Document"] = relationship(back_populates="options")


class Section(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sections"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(512))
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # heading depth
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excluded: Mapped[bool] = mapped_column(default=False, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="sections")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="Chunk.position"
    )


class Chunk(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chunks"

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)

    section: Mapped["Section"] = relationship(back_populates="chunks")
