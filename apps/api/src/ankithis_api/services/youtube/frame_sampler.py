"""Scene-based frame sampling using pixel-diff heuristics."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Threshold for scene change detection (0-1, higher = more sensitive)
SCENE_THRESHOLD = 0.30


def detect_scene_changes(
    video_path: str | Path,
    threshold: float = SCENE_THRESHOLD,
) -> list[float]:
    """Detect scene change timestamps using ffmpeg's scene detection filter.

    Returns list of timestamps (seconds) where scene changes occur.
    Uses ffmpeg's select filter with scene detection — no ML needed.
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(video_path),
                "-vf",
                f"select='gt(scene,{threshold})',showinfo",
                "-vsync",
                "vfr",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        # Parse timestamps from showinfo output
        timestamps = []
        for line in result.stderr.split("\n"):
            if "pts_time:" in line:
                try:
                    pts = line.split("pts_time:")[1].split()[0]
                    timestamps.append(float(pts))
                except (IndexError, ValueError):
                    continue
        return timestamps
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        logger.warning("Scene detection failed", exc_info=True)
        return []


def sample_frames_at_transitions(
    video_path: str | Path,
    scene_timestamps: list[float],
    max_frames: int = 30,
) -> list[tuple[float, bytes]]:
    """Extract frames at scene transition points.

    Returns list of (timestamp, jpeg_bytes) tuples.
    If too many scenes, sample evenly from the scene list.
    """
    if not scene_timestamps:
        return []

    # Limit number of frames
    if len(scene_timestamps) > max_frames:
        step = len(scene_timestamps) / max_frames
        scene_timestamps = [scene_timestamps[int(i * step)] for i in range(max_frames)]

    frames = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for ts in scene_timestamps:
            frame_path = Path(tmpdir) / f"scene_{ts:.2f}.jpg"
            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-ss",
                        f"{ts:.2f}",
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
                    frames.append((ts, frame_path.read_bytes()))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue

    return frames


def sample_frames_uniform(
    video_path: str | Path,
    duration_seconds: int,
    interval: int = 30,
) -> list[tuple[float, bytes]]:
    """Fallback: sample one frame every `interval` seconds.

    Used when scene detection fails or for dense sampling mode.
    Returns list of (timestamp, jpeg_bytes) tuples.
    """
    if duration_seconds <= 0:
        return []

    timestamps = list(range(interval, duration_seconds, interval))
    frames = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for ts in timestamps:
            frame_path = Path(tmpdir) / f"uniform_{ts}.jpg"
            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-ss",
                        str(ts),
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
                    frames.append((float(ts), frame_path.read_bytes()))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue

    return frames
