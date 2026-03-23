"""Fetch YouTube video metadata using yt-dlp."""

from __future__ import annotations

import logging
import re

import yt_dlp

logger = logging.getLogger(__name__)

_YOUTUBE_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})"
)


def extract_video_id(url: str) -> str | None:
    """Extract the 11-character video ID from a YouTube URL."""
    match = _YOUTUBE_PATTERN.search(url)
    return match.group(1) if match else None


def fetch_metadata(url: str) -> dict:
    """Fetch video metadata without downloading.

    Returns dict with keys:
        video_id, title, channel, duration_seconds, description,
        has_manual_captions, chapter_markers, language, thumbnail_url
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Invalid YouTube URL: {url}")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # Parse chapter markers
    chapters = []
    for ch in info.get("chapters") or []:
        chapters.append(
            {
                "title": ch.get("title", ""),
                "start_time": ch.get("start_time", 0),
                "end_time": ch.get("end_time"),
            }
        )

    # Check for manual captions
    subtitles = info.get("subtitles") or {}
    automatic_captions = info.get("automatic_captions") or {}
    has_manual = bool(subtitles)  # manual captions exist

    return {
        "video_id": video_id,
        "title": info.get("title", ""),
        "channel": info.get("channel") or info.get("uploader", ""),
        "duration_seconds": info.get("duration") or 0,
        "description": info.get("description", ""),
        "has_manual_captions": has_manual,
        "has_auto_captions": bool(automatic_captions),
        "chapter_markers": chapters,
        "language": info.get("language") or "en",
        "thumbnail_url": info.get("thumbnail", ""),
    }
