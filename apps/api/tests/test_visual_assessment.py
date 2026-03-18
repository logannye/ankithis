from ankithis_api.services.youtube.visual_assessment import (
    DEFAULT_ASSESSMENT, SAMPLE_FRAME_COUNT,
)
from ankithis_api.llm.schemas import VisualAssessmentOutput, schema_for


def test_default_assessment_has_all_fields():
    assert "visual_density" in DEFAULT_ASSESSMENT
    assert "video_type" in DEFAULT_ASSESSMENT
    assert "recommended_sampling" in DEFAULT_ASSESSMENT
    assert DEFAULT_ASSESSMENT["visual_density"] == "low"
    assert DEFAULT_ASSESSMENT["recommended_sampling"] == "skip"


def test_sample_frame_count():
    assert SAMPLE_FRAME_COUNT == 6


def test_visual_assessment_schema_validates():
    data = {
        "visual_density": "high",
        "video_type": "whiteboard",
        "frame_information": "Dense equations and diagrams on whiteboard",
        "recommended_sampling": "dense",
    }
    output = VisualAssessmentOutput.model_validate(data)
    assert output.visual_density == "high"
    assert output.recommended_sampling == "dense"


def test_visual_assessment_schema_has_fields():
    schema = schema_for(VisualAssessmentOutput)
    props = schema["properties"]
    assert "visual_density" in props
    assert "video_type" in props
    assert "recommended_sampling" in props
