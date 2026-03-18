"""Section a YouTube transcript into logical segments."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Transition phrases that signal a new topic
_TRANSITION_PATTERNS = re.compile(
    r"(?:now let'?s|moving on to|next (?:we'?ll|topic|up)|"
    r"let'?s (?:talk about|look at|move on)|"
    r"the next (?:thing|topic|section)|"
    r"so that'?s .{5,30}(?:now|next)|"
    r"okay so|alright so|"
    r"turning (?:now )?to)",
    re.I,
)


def section_by_chapters(
    segments: list[dict],
    chapters: list[dict],
) -> list[dict]:
    """Section transcript using YouTube chapter markers.

    Args:
        segments: Timestamped transcript segments [{start, duration, text}]
        chapters: Chapter markers [{title, start_time, end_time}]

    Returns:
        List of sections: [{title, start_time, end_time, text}]
    """
    if not chapters or not segments:
        return []

    sections = []
    for ch in chapters:
        ch_start = ch["start_time"]
        ch_end = ch.get("end_time") or float("inf")

        # Collect segments within this chapter
        chapter_text = []
        for seg in segments:
            seg_start = seg["start"]
            if ch_start <= seg_start < ch_end:
                chapter_text.append(seg["text"])

        if chapter_text:
            sections.append({
                "title": ch["title"],
                "start_time": ch_start,
                "end_time": ch_end,
                "text": " ".join(chapter_text),
            })

    return sections


def section_by_topic_shifts(
    segments: list[dict],
    min_section_words: int = 200,
) -> list[dict]:
    """Section transcript by detecting topic shifts.

    Uses transition phrases and long pauses to find section boundaries.
    Falls back to time-based sectioning if no shifts are detected.

    Args:
        segments: Timestamped transcript segments [{start, duration, text}]
        min_section_words: Minimum words per section to avoid tiny sections

    Returns:
        List of sections: [{title, start_time, end_time, text}]
    """
    if not segments:
        return []

    # Find potential break points
    breaks: list[int] = [0]  # Always start with first segment

    for i in range(1, len(segments)):
        seg = segments[i]
        prev = segments[i - 1]

        # Check for long pause (> 3 seconds gap)
        gap = seg["start"] - (prev["start"] + prev["duration"])
        if gap > 3.0:
            breaks.append(i)
            continue

        # Check for transition phrase
        if _TRANSITION_PATTERNS.search(seg["text"]):
            breaks.append(i)
            continue

    # If no breaks found (or just the initial one), fall back to time-based
    if len(breaks) <= 1:
        return _section_by_time(segments)

    # Merge tiny sections into previous
    merged_breaks = [breaks[0]]
    for b in breaks[1:]:
        # Count words since last break
        words = sum(
            len(segments[j]["text"].split())
            for j in range(merged_breaks[-1], b)
        )
        if words >= min_section_words:
            merged_breaks.append(b)

    # Build sections
    sections = []
    for idx, start_idx in enumerate(merged_breaks):
        end_idx = merged_breaks[idx + 1] if idx + 1 < len(merged_breaks) else len(segments)
        section_segments = segments[start_idx:end_idx]

        if not section_segments:
            continue

        text = " ".join(s["text"] for s in section_segments)
        sections.append({
            "title": f"Section {idx + 1}",
            "start_time": section_segments[0]["start"],
            "end_time": section_segments[-1]["start"] + section_segments[-1]["duration"],
            "text": text,
        })

    return sections


def _section_by_time(
    segments: list[dict],
    section_duration: float = 300.0,  # 5 minutes per section
) -> list[dict]:
    """Fallback: split transcript into fixed-duration sections."""
    if not segments:
        return []

    total_duration = segments[-1]["start"] + segments[-1]["duration"]
    num_sections = max(1, int(total_duration / section_duration))
    section_len = total_duration / num_sections

    sections = []
    for i in range(num_sections):
        start_t = i * section_len
        end_t = (i + 1) * section_len

        section_text = []
        for seg in segments:
            if start_t <= seg["start"] < end_t:
                section_text.append(seg["text"])

        if section_text:
            sections.append({
                "title": f"Part {i + 1}",
                "start_time": start_t,
                "end_time": end_t,
                "text": " ".join(section_text),
            })

    return sections
