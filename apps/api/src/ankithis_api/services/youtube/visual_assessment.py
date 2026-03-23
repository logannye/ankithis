"""Assess visual information density of a YouTube video."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.prompts.visual_assess import SYSTEM, USER_TEMPLATE
from ankithis_api.llm.schemas import VisualAssessmentOutput, schema_for

logger = logging.getLogger(__name__)

DEFAULT_ASSESSMENT: dict = {
    "visual_density": "low",
    "video_type": "talking_head",
    "frame_information": "Unable to assess visuals",
    "recommended_sampling": "skip",
}

SAMPLE_FRAME_COUNT = 6


def download_video(url: str, dest: Path) -> bool:
    """Download a video to *dest* using yt-dlp (lowest quality).

    Returns True on success.
    """
    try:
        subprocess.run(
            [
                "yt-dlp",
                "-f",
                "worstvideo[ext=mp4]/worst[ext=mp4]/worst",
                "-o",
                str(dest),
                "--quiet",
                "--no-warnings",
                url,
            ],
            check=True,
            timeout=120,
            capture_output=True,
        )
        return dest.exists()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.warning("Failed to download video for frame extraction")
        return False


def extract_frames_from_file(
    video_path: Path,
    duration_seconds: int,
    count: int = SAMPLE_FRAME_COUNT,
) -> list[bytes]:
    """Extract evenly-spaced sample frames from a local video file.

    Returns list of JPEG image bytes.
    """
    if duration_seconds <= 0 or not video_path.exists():
        return []

    interval = duration_seconds / (count + 1)
    timestamps = [interval * (i + 1) for i in range(count)]

    frames: list[bytes] = []
    tmpdir = video_path.parent  # reuse the same temp directory
    for ts in timestamps:
        frame_path = tmpdir / f"frame_{ts:.1f}.jpg"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-ss",
                    f"{ts:.1f}",
                    "-i",
                    str(video_path),
                    "-frames:v",
                    "1",
                    "-q:v",
                    "5",
                    str(frame_path),
                    "-y",
                ],
                check=True,
                timeout=30,
                capture_output=True,
            )
            if frame_path.exists():
                frames.append(frame_path.read_bytes())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            logger.debug("Failed to extract frame at %.1f", ts)
            continue

    return frames


def extract_sample_frames(
    url: str,
    duration_seconds: int,
    count: int = SAMPLE_FRAME_COUNT,
) -> list[bytes]:
    """Extract evenly-spaced sample frames from a video using yt-dlp + ffmpeg.

    Returns list of JPEG image bytes.
    Downloads the video to a temporary directory, then delegates to
    :func:`extract_frames_from_file`.
    """
    if duration_seconds <= 0:
        return []

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = Path(tmpdir) / "video.mp4"
        if not download_video(url, video_path):
            return []
        return extract_frames_from_file(video_path, duration_seconds, count)


def assess_visuals(
    url: str,
    duration_seconds: int,
    title: str = "",
    video_path: Path | None = None,
) -> dict:
    """Assess visual information density of a YouTube video.

    Samples 6 frames, sends to multimodal LLM for analysis.
    Returns assessment dict. Falls back to DEFAULT_ASSESSMENT on any failure.

    If *video_path* is provided (an already-downloaded local file), frames are
    extracted directly from it instead of re-downloading the video.
    """
    try:
        if video_path and video_path.exists():
            frames = extract_frames_from_file(video_path, duration_seconds)
        else:
            frames = extract_sample_frames(url, duration_seconds)

        if not frames:
            logger.info("No frames extracted, defaulting to low visual density")
            return dict(DEFAULT_ASSESSMENT)

        user_text = USER_TEMPLATE.format(
            frame_count=len(frames),
            title=title,
            duration=duration_seconds,
        )

        result = structured_call(
            system=SYSTEM,
            user=user_text,
            tool_name="assess_visuals",
            tool_schema=schema_for(VisualAssessmentOutput),
            model=settings.bedrock_model,
            images=frames,
        )
        output = VisualAssessmentOutput.model_validate(result)
        return output.model_dump()

    except Exception:
        logger.warning("Visual assessment failed, using defaults", exc_info=True)
        return dict(DEFAULT_ASSESSMENT)
