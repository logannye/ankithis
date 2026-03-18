from ankithis_api.services.youtube.sectioner import (
    section_by_chapters,
    section_by_topic_shifts,
)
from ankithis_api.services.youtube.assembler import (
    assemble_chunks,
    _split_into_paragraphs,
)


def test_section_by_chapters():
    segments = [
        {"start": 0, "duration": 5, "text": "Hello welcome"},
        {"start": 5, "duration": 5, "text": "to the lecture"},
        {"start": 60, "duration": 5, "text": "Now chapter two"},
        {"start": 65, "duration": 5, "text": "covers enzymes"},
    ]
    chapters = [
        {"title": "Introduction", "start_time": 0, "end_time": 60},
        {"title": "Enzymes", "start_time": 60, "end_time": 120},
    ]
    sections = section_by_chapters(segments, chapters)
    assert len(sections) == 2
    assert sections[0]["title"] == "Introduction"
    assert "Hello welcome" in sections[0]["text"]
    assert sections[1]["title"] == "Enzymes"
    assert "enzymes" in sections[1]["text"]


def test_section_by_chapters_empty():
    assert section_by_chapters([], []) == []
    assert section_by_chapters([{"start": 0, "duration": 1, "text": "hi"}], []) == []


def test_section_by_topic_shifts_with_pause():
    segments = [
        {"start": 0, "duration": 2, "text": "First topic here. " * 30},
        {"start": 2, "duration": 2, "text": "More first topic. " * 30},
        # 5 second gap triggers break
        {"start": 9, "duration": 2, "text": "Second topic now. " * 30},
        {"start": 11, "duration": 2, "text": "More second topic. " * 30},
    ]
    sections = section_by_topic_shifts(segments, min_section_words=10)
    assert len(sections) >= 2


def test_section_by_topic_shifts_empty():
    assert section_by_topic_shifts([]) == []


def test_assemble_chunks_basic():
    sections = [
        {"title": "Intro", "start_time": 0, "end_time": 60, "text": "Hello world. This is a test."},
    ]
    result = assemble_chunks(sections)
    assert len(result) == 1
    parsed, visuals = result[0]
    assert parsed.title == "Intro"
    assert parsed.level == 1
    assert len(parsed.paragraphs) >= 1


def test_assemble_chunks_with_visual_context():
    sections = [
        {"title": "Enzymes", "start_time": 60, "end_time": 120, "text": "Enzymes catalyze reactions."},
    ]
    annotations = [
        {"timestamp": 70.0, "visual_content": "Diagram of enzyme-substrate complex", "content_type": "diagram", "additive_value": "high"},
        {"timestamp": 200.0, "visual_content": "Unrelated frame", "content_type": "text_slide", "additive_value": "low"},
    ]
    result = assemble_chunks(sections, frame_annotations=annotations)
    assert len(result) == 1
    _, visuals = result[0]
    assert len(visuals) == 1
    assert "enzyme-substrate" in visuals[0]


def test_assemble_chunks_empty():
    assert assemble_chunks([]) == []


def test_split_into_paragraphs():
    text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
    paragraphs = _split_into_paragraphs(text, target_words=5)
    assert len(paragraphs) >= 2
    # All text should be preserved
    rejoined = " ".join(paragraphs)
    assert "First sentence" in rejoined
    assert "Fifth sentence" in rejoined


def test_split_into_paragraphs_empty():
    assert _split_into_paragraphs("") == []
