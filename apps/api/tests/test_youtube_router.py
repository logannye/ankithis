"""Unit tests for the YouTube intake router."""

from ankithis_api.services.youtube.metadata import extract_video_id


def test_youtube_url_standard():
    """Standard youtube.com watch URL."""
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_youtube_url_short():
    """Short youtu.be URL."""
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_youtube_url_invalid():
    """Non-YouTube URLs return None."""
    assert extract_video_id("not-a-url") is None
    assert extract_video_id("https://example.com/watch?v=abc") is None


def test_youtube_url_no_protocol():
    """URL without protocol."""
    assert extract_video_id("www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_duration_limits():
    """Verify duration constants are reasonable."""
    from ankithis_api.routers.youtube import MAX_DURATION, WARN_DURATION

    assert MAX_DURATION == 3 * 60 * 60  # 3 hours
    assert WARN_DURATION == 90 * 60  # 90 minutes
    assert WARN_DURATION < MAX_DURATION


def test_youtube_request_validation():
    """YouTubeRequest rejects invalid URLs."""
    from pydantic import ValidationError

    from ankithis_api.routers.youtube import YouTubeRequest

    # Valid URL should work
    req = YouTubeRequest(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert req.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Invalid URL should raise
    try:
        YouTubeRequest(url="not-a-youtube-url")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass


def test_youtube_upload_response_model():
    """YouTubeUploadResponse serializes correctly."""
    from ankithis_api.routers.youtube import YouTubeUploadResponse

    resp = YouTubeUploadResponse(
        document_id="abc-123",
        filename="Test Video.youtube",
        file_type="youtube",
        section_count=3,
        chunk_count=10,
        word_count=5000,
    )
    assert resp.document_id == "abc-123"
    assert resp.file_type == "youtube"
