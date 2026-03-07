"""Document parser dispatcher. Routes to the appropriate parser by file type."""

from __future__ import annotations

from dataclasses import dataclass, field

from ankithis_api.models.enums import FileType


@dataclass
class ParsedSection:
    title: str | None
    level: int
    paragraphs: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)

    @property
    def word_count(self) -> int:
        return sum(len(p.split()) for p in self.paragraphs)


@dataclass
class ParseResult:
    sections: list[ParsedSection]
    page_count: int | None = None
    word_count: int = 0

    def __post_init__(self):
        self.word_count = sum(s.word_count for s in self.sections)


def parse_document(file_path: str, file_type: FileType) -> ParseResult:
    """Parse a document into sections based on file type."""
    if file_type == FileType.PDF:
        from ankithis_api.services.parsers.pdf_parser import parse_pdf

        raw_sections, page_count = parse_pdf(file_path)
        sections = [
            ParsedSection(title=s.title, level=s.level, paragraphs=s.paragraphs)
            for s in raw_sections
        ]
        return ParseResult(sections=sections, page_count=page_count)

    elif file_type == FileType.DOCX:
        from ankithis_api.services.parsers.docx_parser import parse_docx

        raw_sections = parse_docx(file_path)
        sections = [
            ParsedSection(title=s.title, level=s.level, paragraphs=s.paragraphs)
            for s in raw_sections
        ]
        return ParseResult(sections=sections)

    elif file_type == FileType.MD:
        from ankithis_api.services.parsers.text_parser import parse_markdown

        raw_sections = parse_markdown(file_path)
        sections = [
            ParsedSection(title=s.title, level=s.level, paragraphs=s.paragraphs)
            for s in raw_sections
        ]
        return ParseResult(sections=sections)

    elif file_type == FileType.TXT:
        from ankithis_api.services.parsers.text_parser import parse_text

        raw_sections = parse_text(file_path)
        sections = [
            ParsedSection(title=s.title, level=s.level, paragraphs=s.paragraphs)
            for s in raw_sections
        ]
        return ParseResult(sections=sections)

    else:
        raise ValueError(f"Unsupported file type: {file_type}")
