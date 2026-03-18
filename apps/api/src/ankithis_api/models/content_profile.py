"""ContentProfile — document-level classification from Stage 0."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON

from ankithis_api.models.base import Base, UUIDMixin, TimestampMixin
from ankithis_api.models.enums import (
    ContentType, Difficulty, InformationDensity,
    StructureQuality, KnowledgeType,
)


class ContentProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "content_profiles"

    document_id = sa.Column(
        sa.UUID, ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    content_type = sa.Column(sa.Enum(ContentType), nullable=False)
    domain = sa.Column(sa.String(200), nullable=False, default="general")
    difficulty = sa.Column(sa.Enum(Difficulty), nullable=False, default=Difficulty.INTERMEDIATE)
    information_density = sa.Column(
        sa.Enum(InformationDensity), nullable=False, default=InformationDensity.MODERATE,
    )
    structure_quality = sa.Column(
        sa.Enum(StructureQuality), nullable=False, default=StructureQuality.SEMI_STRUCTURED,
    )
    primary_knowledge_type = sa.Column(
        sa.Enum(KnowledgeType), nullable=False, default=KnowledgeType.MIXED,
    )
    recommended_cloze_ratio = sa.Column(sa.Float, nullable=False, default=0.5)
    recommended_qa_ratio = sa.Column(sa.Float, nullable=False, default=0.5)
    special_considerations = sa.Column(JSON, nullable=False, server_default="[]")
