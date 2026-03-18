"""Analyze video frames for educational content using multimodal LLM."""

from __future__ import annotations

import json
import logging

from ankithis_api.config import settings
from ankithis_api.llm.client import structured_call
from ankithis_api.llm.schemas import schema_for

from pydantic import BaseModel

logger = logging.getLogger(__name__)

BATCH_SIZE = 5  # frames per LLM call


class FrameAnnotation(BaseModel):
    timestamp: float
    visual_content: str
    content_type: str  # text_slide, diagram, equation, code, table, photo, none
    additive_value: str  # none, low, high


class FrameAnalysisOutput(BaseModel):
    annotations: list[FrameAnnotation]


_SYSTEM = """\
You are an expert at extracting educational content from video frames. \
For each frame, extract any text, diagrams, equations, code, or visual \
information that is NOT already captured in the surrounding transcript.

Only report ADDITIVE information — if the frame shows bullet points that \
the speaker reads verbatim, that adds nothing. If the frame shows a diagram \
while the speaker says "and then this group attacks here", the visual adds \
everything.

For each frame, report:
- visual_content: What the frame shows (extracted text, diagram description, etc.)
- content_type: text_slide, diagram, equation, code, table, photo, or none
- additive_value: none (transcript covers it), low (minor addition), high (critical visual info)
"""

_USER_TEMPLATE = """\
Analyze these video frames. For each frame, extract visual information \
not captured in the transcript.

{frame_descriptions}

Return an annotation for each frame.
"""


def analyze_frames(
    frames: list[tuple[float, bytes]],
    transcript_context: dict[float, str] | None = None,
) -> list[dict]:
    """Analyze video frames in batches using multimodal LLM.

    Args:
        frames: List of (timestamp, jpeg_bytes) tuples
        transcript_context: Optional dict mapping timestamps to nearby transcript text

    Returns:
        List of annotation dicts with additive_value != "none" only.
    """
    if not frames:
        return []

    all_annotations: list[dict] = []

    for i in range(0, len(frames), BATCH_SIZE):
        batch = frames[i : i + BATCH_SIZE]
        image_bytes_list = [frame_bytes for _, frame_bytes in batch]

        # Build frame descriptions with transcript context
        descriptions = []
        for ts, _ in batch:
            ctx = ""
            if transcript_context and ts in transcript_context:
                ctx = f" Transcript around this time: \"{transcript_context[ts]}\""
            descriptions.append(f"- Frame at {ts:.1f}s{ctx}")

        user = _USER_TEMPLATE.format(frame_descriptions="\n".join(descriptions))

        try:
            result = structured_call(
                system=_SYSTEM,
                user=user,
                tool_name="analyze_frames",
                tool_schema=schema_for(FrameAnalysisOutput),
                model=settings.bedrock_model,
                images=image_bytes_list,
            )
            output = FrameAnalysisOutput.model_validate(result)

            # Only keep frames with additive value
            for ann in output.annotations:
                if ann.additive_value != "none":
                    all_annotations.append(ann.model_dump())

        except Exception:
            logger.warning("Frame analysis batch failed (frames %d-%d)", i, i + len(batch), exc_info=True)
            continue

    logger.info("Frame analysis: %d frames analyzed, %d with additive value",
                len(frames), len(all_annotations))
    return all_annotations
