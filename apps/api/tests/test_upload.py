"""Tests for the upload endpoint using a mock DB."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ankithis_api.app import app
from ankithis_api.db import get_db

client = TestClient(app)


def _mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture(autouse=False)
def mock_db():
    session = _mock_db_session()

    async def override():
        yield session

    app.dependency_overrides[get_db] = override
    yield session
    app.dependency_overrides.clear()


def test_upload_unsupported_type():
    """Uploading an unsupported file type returns 422."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.exe", b"binary content", "application/octet-stream")},
    )
    assert response.status_code == 422


def test_upload_empty_file():
    """Uploading an empty file returns 422."""
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"", "text/plain")},
    )
    assert response.status_code == 422


@patch("ankithis_api.routers.upload.save_upload")
@patch("ankithis_api.routers.upload.parse_document")
def test_upload_txt_success(mock_parse, mock_save, mock_db):
    """Uploading a valid TXT file succeeds."""
    from ankithis_api.services.parser import ParsedSection, ParseResult

    mock_save.return_value = "/tmp/test.txt"
    mock_parse.return_value = ParseResult(
        sections=[
            ParsedSection(
                title="Test Section",
                level=1,
                paragraphs=["A paragraph with enough words to be meaningful."],
            )
        ],
        page_count=None,
    )

    response = client.post(
        "/api/upload",
        files={"file": ("notes.txt", b"some content here", "text/plain")},
        data={"card_style": "cloze_heavy", "deck_size": "medium"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "notes.txt"
    assert data["file_type"] == "txt"
    assert data["section_count"] == 1


@patch("ankithis_api.routers.upload.save_upload")
@patch("ankithis_api.routers.upload.parse_document")
def test_upload_md_success(mock_parse, mock_save, mock_db):
    """Uploading a valid MD file succeeds."""
    from ankithis_api.services.parser import ParsedSection, ParseResult

    mock_save.return_value = "/tmp/test.md"
    mock_parse.return_value = ParseResult(
        sections=[
            ParsedSection(title="Intro", level=1, paragraphs=["Content here."]),
            ParsedSection(title="Methods", level=2, paragraphs=["More content."]),
        ],
    )

    response = client.post(
        "/api/upload",
        files={"file": ("study.md", b"# Intro\ncontent", "text/markdown")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["section_count"] == 2
    assert data["file_type"] == "md"
