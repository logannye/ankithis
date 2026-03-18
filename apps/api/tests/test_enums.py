from ankithis_api.models.enums import (
    ContentType, Difficulty, InformationDensity, StructureQuality,
    KnowledgeType, PedagogicalFunction, VisualDensity, VideoType, FileType,
)


def test_content_type_values():
    assert ContentType.LECTURE_SLIDES == "lecture_slides"
    assert ContentType.RESEARCH_PAPER == "research_paper"
    assert ContentType.TEXTBOOK_CHAPTER == "textbook_chapter"
    assert ContentType.PERSONAL_NOTES == "personal_notes"
    assert ContentType.TECHNICAL_DOCS == "technical_docs"
    assert ContentType.GENERAL_ARTICLE == "general_article"
    assert ContentType.VIDEO_LECTURE == "video_lecture"
    assert ContentType.VIDEO_TUTORIAL == "video_tutorial"
    assert ContentType.VIDEO_DEMO == "video_demo"


def test_difficulty_values():
    assert Difficulty.INTRODUCTORY == "introductory"
    assert Difficulty.EXPERT == "expert"


def test_information_density_values():
    assert InformationDensity.SPARSE == "sparse"
    assert InformationDensity.VERY_DENSE == "very_dense"


def test_structure_quality_values():
    assert StructureQuality.WELL_STRUCTURED == "well_structured"
    assert StructureQuality.UNSTRUCTURED == "unstructured"


def test_knowledge_type_values():
    assert KnowledgeType.FACTUAL == "factual"
    assert KnowledgeType.MIXED == "mixed"


def test_pedagogical_function_values():
    assert PedagogicalFunction.DEFINITIONS == "definitions"
    assert PedagogicalFunction.THEORY == "theory"
    assert PedagogicalFunction.METHODOLOGY == "methodology"
    assert PedagogicalFunction.EXAMPLES == "examples"
    assert PedagogicalFunction.DATA_RESULTS == "data_results"
    assert PedagogicalFunction.SUMMARY == "summary"
    assert PedagogicalFunction.CODE == "code"
    assert PedagogicalFunction.ENUMERATION == "enumeration"
    assert PedagogicalFunction.UNKNOWN == "unknown"


def test_visual_density_values():
    assert VisualDensity.LOW == "low"
    assert VisualDensity.HIGH == "high"


def test_video_type_values():
    assert VideoType.TALKING_HEAD == "talking_head"
    assert VideoType.SLIDES_WITH_SPEAKER == "slides_with_speaker"


def test_file_type_includes_youtube():
    assert FileType.YOUTUBE == "youtube"
