from ankithis_api.models.content_profile import ContentProfile
from ankithis_api.models.video_source import VideoSource
from ankithis_api.models.document import Section, Chunk

def test_content_profile_has_columns():
    cols = {c.name for c in ContentProfile.__table__.columns}
    assert "content_type" in cols
    assert "domain" in cols
    assert "difficulty" in cols
    assert "information_density" in cols
    assert "structure_quality" in cols
    assert "primary_knowledge_type" in cols
    assert "recommended_cloze_ratio" in cols
    assert "recommended_qa_ratio" in cols
    assert "special_considerations" in cols
    assert "document_id" in cols

def test_video_source_has_columns():
    cols = {c.name for c in VideoSource.__table__.columns}
    assert "youtube_url" in cols
    assert "video_id" in cols
    assert "title" in cols
    assert "channel" in cols
    assert "duration_seconds" in cols
    assert "visual_density" in cols
    assert "video_type" in cols
    assert "chapter_markers" in cols
    assert "document_id" in cols

def test_section_has_pedagogical_function():
    cols = {c.name for c in Section.__table__.columns}
    assert "pedagogical_function" in cols

def test_chunk_has_visual_context():
    cols = {c.name for c in Chunk.__table__.columns}
    assert "visual_context" in cols
