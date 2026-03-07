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


class CardStyle(str, enum.Enum):
    CLOZE_HEAVY = "cloze_heavy"
    QA_HEAVY = "qa_heavy"
    BALANCED = "balanced"


class DeckSize(str, enum.Enum):
    SMALL = "small"      # 30-50 cards
    MEDIUM = "medium"    # 80-150 cards
    LARGE = "large"      # 200-300 cards


class CardType(str, enum.Enum):
    CLOZE = "cloze"
    BASIC = "basic"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
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
