import os
import tempfile

from ankithis_api.services.parsers.text_parser import parse_markdown, parse_text


def test_parse_markdown_headings():
    """Markdown parser splits on # headings."""
    content = "# Introduction\n\nSome intro text.\n\n## Methods\n\nMethod details here.\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        sections = parse_markdown(f.name)
    os.unlink(f.name)

    assert len(sections) == 2
    assert sections[0].title == "Introduction"
    assert sections[0].level == 1
    assert sections[1].title == "Methods"
    assert sections[1].level == 2


def test_parse_markdown_body():
    """Paragraphs are captured in the correct sections."""
    content = "# Title\n\nFirst paragraph.\n\nSecond paragraph.\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        sections = parse_markdown(f.name)
    os.unlink(f.name)

    assert len(sections) == 1
    assert len(sections[0].paragraphs) == 2
    assert "First paragraph" in sections[0].paragraphs[0]


def test_parse_plain_text():
    """Plain text parser handles simple content."""
    content = "This is line one.\nThis is line two.\nThis is line three.\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        f.flush()
        sections = parse_text(f.name)
    os.unlink(f.name)

    assert len(sections) >= 1
    total_paragraphs = sum(len(s.paragraphs) for s in sections)
    assert total_paragraphs == 3


def test_parse_text_with_caps_heading():
    """ALL CAPS lines are detected as headings in plain text."""
    content = "INTRODUCTION\n\nSome text here.\n\nMETHODS\n\nMore text here.\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        f.flush()
        sections = parse_text(f.name)
    os.unlink(f.name)

    assert len(sections) == 2
    assert sections[0].title == "INTRODUCTION"
    assert sections[1].title == "METHODS"


def test_empty_file():
    """Empty file returns one empty section."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("")
        f.flush()
        sections = parse_text(f.name)
    os.unlink(f.name)

    assert len(sections) == 1
