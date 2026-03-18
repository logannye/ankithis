"""VideoSource — metadata for YouTube-sourced documents."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSON

from ankithis_api.models.base import Base, UUIDMixin, TimestampMixin
from ankithis_api.models.enums import VisualDensity, VideoType


class VideoSource(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "video_sources"

    document_id = sa.Column(
        sa.UUID, ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    youtube_url = sa.Column(sa.String(500), nullable=False)
    video_id = sa.Column(sa.String(20), nullable=False)
    title = sa.Column(sa.String(500), nullable=False)
    channel = sa.Column(sa.String(200), nullable=True)
    duration_seconds = sa.Column(sa.Integer, nullable=False)
    has_manual_captions = sa.Column(sa.Boolean, nullable=False, default=False)
    visual_density = sa.Column(sa.Enum(VisualDensity), nullable=True)
    video_type = sa.Column(sa.Enum(VideoType), nullable=True)
    chapter_markers = sa.Column(JSON, nullable=False, server_default="[]")
