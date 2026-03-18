from ankithis_api.services.youtube.metadata import extract_video_id

def test_extract_video_id_standard_url():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

def test_extract_video_id_short_url():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

def test_extract_video_id_with_params():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42") == "dQw4w9WgXcQ"

def test_extract_video_id_invalid():
    assert extract_video_id("https://example.com/not-youtube") is None

def test_extract_video_id_empty():
    assert extract_video_id("") is None

def test_extract_video_id_no_protocol():
    assert extract_video_id("youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
