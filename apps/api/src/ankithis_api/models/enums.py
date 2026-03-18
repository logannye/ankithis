import enum


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    YOUTUBE = "youtube"


class CardStyle(str, enum.Enum):
    CLOZE_HEAVY = "cloze_heavy"
    QA_HEAVY = "qa_heavy"
    BALANCED = "balanced"


class DeckSize(str, enum.Enum):
    SMALL = "small"  # ~5 cards per 1K words — key concepts only
    MEDIUM = "medium"  # ~12 cards per 1K words — solid coverage
    LARGE = "large"  # ~22 cards per 1K words — deep, thorough coverage


class CardType(str, enum.Enum):
    CLOZE = "cloze"
    BASIC = "basic"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    CLASSIFYING = "classifying"  # Stage 0: content classification
    FETCHING_VIDEO = "fetching_video"  # YouTube: download video
    EXTRACTING_TRANSCRIPT = "extracting_transcript"  # YouTube: extract transcript
    ANALYZING_VISUALS = "analyzing_visuals"  # YouTube: analyze visual frames
    STAGE_A = "stage_a"  # concept extraction
    STAGE_B = "stage_b"  # concept merge
    STAGE_C = "stage_c"  # card planning
    STAGE_D = "stage_d"  # card generation
    STAGE_E = "stage_e"  # critique
    STAGE_F = "stage_f"  # dedup
    QC = "qc"
    COMPLETED = "completed"
    FAILED = "failed"


class CritiqueVerdict(str, enum.Enum):
    PASS = "pass"
    REWRITE = "rewrite"
    SUPPRESS = "suppress"


class ContentType(str, enum.Enum):
    LECTURE_SLIDES = "lecture_slides"
    RESEARCH_PAPER = "research_paper"
    TEXTBOOK_CHAPTER = "textbook_chapter"
    PERSONAL_NOTES = "personal_notes"
    TECHNICAL_DOCS = "technical_docs"
    GENERAL_ARTICLE = "general_article"
    VIDEO_LECTURE = "video_lecture"
    VIDEO_TUTORIAL = "video_tutorial"
    VIDEO_DEMO = "video_demo"


class Difficulty(str, enum.Enum):
    INTRODUCTORY = "introductory"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class InformationDensity(str, enum.Enum):
    SPARSE = "sparse"
    MODERATE = "moderate"
    DENSE = "dense"
    VERY_DENSE = "very_dense"


class StructureQuality(str, enum.Enum):
    WELL_STRUCTURED = "well_structured"
    SEMI_STRUCTURED = "semi_structured"
    UNSTRUCTURED = "unstructured"


class KnowledgeType(str, enum.Enum):
    FACTUAL = "factual"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    MIXED = "mixed"


class PedagogicalFunction(str, enum.Enum):
    DEFINITIONS = "definitions"
    THEORY = "theory"
    METHODOLOGY = "methodology"
    EXAMPLES = "examples"
    DATA_RESULTS = "data_results"
    SUMMARY = "summary"
    CODE = "code"
    ENUMERATION = "enumeration"
    UNKNOWN = "unknown"


class VisualDensity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VideoType(str, enum.Enum):
    TALKING_HEAD = "talking_head"
    SLIDES_WITH_SPEAKER = "slides_with_speaker"
    SCREENCAST = "screencast"
    WHITEBOARD = "whiteboard"
    ANIMATION = "animation"
    DEMONSTRATION = "demonstration"
    MIXED = "mixed"
