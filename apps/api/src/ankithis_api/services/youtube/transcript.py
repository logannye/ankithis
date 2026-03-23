"""Extract transcripts from YouTube videos."""

from __future__ import annotations

import json
import logging
import urllib.request

import yt_dlp

logger = logging.getLogger(__name__)


def extract_transcript(url: str, prefer_manual: bool = True) -> list[dict]:
    """Extract timestamped transcript segments from a YouTube video.

    Returns list of dicts with keys: start, duration, text
    Priority: manual captions > auto-generated captions

    Raises ValueError if no transcript is available.
    """
    # Try manual captions first, then auto-generated
    for auto in [False, True] if prefer_manual else [True, False]:
        try:
            segments = _download_subtitles(url, auto=auto)
            if segments:
                logger.info(
                    "Extracted %d transcript segments (%s)",
                    len(segments),
                    "auto" if auto else "manual",
                )
                return segments
        except Exception:
            logger.debug("Subtitle extraction failed (auto=%s)", auto, exc_info=True)
            continue

    raise ValueError("No transcript available for this video")


def _download_subtitles(url: str, auto: bool = False) -> list[dict]:
    """Download and parse subtitles using yt-dlp."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": not auto,
        "writeautomaticsub": auto,
        "subtitleslangs": ["en"],
        "subtitlesformat": "json3",  # Structured JSON format
    }

    segments = []

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # Get subtitle data
        sub_source = info.get("automatic_captions" if auto else "subtitles") or {}
        en_subs = sub_source.get("en") or sub_source.get("en-US") or []

        # Find json3 format
        json3_url = None
        for sub in en_subs:
            if sub.get("ext") == "json3":
                json3_url = sub.get("url")
                break

        if not json3_url:
            # Fallback: try vtt format and parse
            for sub in en_subs:
                if sub.get("ext") == "vtt":
                    json3_url = sub.get("url")
                    break

        if not json3_url:
            return []

        # Download and parse subtitle data
        with urllib.request.urlopen(json3_url) as resp:
            data = json.loads(resp.read())

        # Parse json3 format
        events = data.get("events", [])
        for event in events:
            if "segs" not in event:
                continue
            text = "".join(seg.get("utf8", "") for seg in event["segs"]).strip()
            if not text or text == "\n":
                continue
            start_ms = event.get("tStartMs", 0)
            duration_ms = event.get("dDurationMs", 0)
            segments.append(
                {
                    "start": start_ms / 1000.0,
                    "duration": duration_ms / 1000.0,
                    "text": text,
                }
            )

    return segments


def transcript_to_text(segments: list[dict]) -> str:
    """Convert transcript segments to plain text."""
    return " ".join(seg["text"] for seg in segments)


def transcript_word_count(segments: list[dict]) -> int:
    """Count total words in transcript."""
    return sum(len(seg["text"].split()) for seg in segments)
