from ankithis_api.services.youtube.frame_analyzer import (
    BATCH_SIZE,
    FrameAnalysisOutput,
    FrameAnnotation,
)
from ankithis_api.services.youtube.frame_sampler import SCENE_THRESHOLD


def test_scene_threshold_reasonable():
    assert 0.1 <= SCENE_THRESHOLD <= 0.5


def test_batch_size():
    assert BATCH_SIZE == 5


def test_frame_annotation_validates():
    ann = FrameAnnotation(
        timestamp=42.5,
        visual_content="Slide shows reaction mechanism with arrow pushing",
        content_type="diagram",
        additive_value="high",
    )
    assert ann.timestamp == 42.5
    assert ann.additive_value == "high"


def test_frame_analysis_output_validates():
    data = {
        "annotations": [
            {
                "timestamp": 10.0,
                "visual_content": "Title slide: Organic Chemistry Lecture 14",
                "content_type": "text_slide",
                "additive_value": "low",
            },
            {
                "timestamp": 45.0,
                "visual_content": "SN2 mechanism diagram with nucleophile attacking",
                "content_type": "diagram",
                "additive_value": "high",
            },
        ]
    }
    output = FrameAnalysisOutput.model_validate(data)
    assert len(output.annotations) == 2
    assert output.annotations[1].content_type == "diagram"
