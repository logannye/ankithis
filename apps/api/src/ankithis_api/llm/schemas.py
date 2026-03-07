"""Pydantic models for LLM structured outputs across all stages."""

from __future__ import annotations

from pydantic import BaseModel, Field


# Stage A: Concept Extraction
class ExtractedConcept(BaseModel):
    name: str = Field(description="Short name for the concept (3-8 words)")
    description: str = Field(description="One-sentence description of what this concept covers")
    importance: int = Field(
        ge=1, le=10, description="Importance for understanding the material (1-10)"
    )
    source_quote: str = Field(
        description="A key quote or phrase from the text supporting this concept"
    )


class ConceptExtractionOutput(BaseModel):
    concepts: list[ExtractedConcept] = Field(description="List of extracted concepts from the text")


# Stage B: Concept Merge
class MergedConcept(BaseModel):
    name: str
    description: str
    importance: int = Field(ge=1, le=10)
    merged_from: list[str] = Field(
        description="Names of original concepts that were merged into this one"
    )


class ConceptMergeOutput(BaseModel):
    concepts: list[MergedConcept] = Field(
        description="Deduplicated and ranked concepts for the section"
    )


# Stage C: Card Planning
class PlannedCard(BaseModel):
    concept_name: str = Field(description="Which concept this card tests")
    card_type: str = Field(description="'cloze' or 'basic'")
    direction: str = Field(description="What specifically this card tests about the concept")
    priority: int = Field(ge=1, le=10, description="How important this card is (1-10)")


class CardPlanOutput(BaseModel):
    cards: list[PlannedCard] = Field(description="Planned cards for these concepts")


# Stage D: Card Generation
class GeneratedCard(BaseModel):
    front: str = Field(
        description="Card front (for cloze: text with {{c1::...}} blanks; for basic: the question)"
    )
    back: str = Field(description="Card back (for cloze: empty string; for basic: the answer)")
    card_type: str = Field(description="'cloze' or 'basic'")
    tags: str = Field(description="Comma-separated tags for this card")


class CardGenerationOutput(BaseModel):
    cards: list[GeneratedCard] = Field(description="Generated flashcards")


# Stage E: Critique
class CritiqueResult(BaseModel):
    card_index: int = Field(description="Index of the card being reviewed (0-based)")
    verdict: str = Field(description="'pass', 'rewrite', or 'suppress'")
    front: str = Field(default="", description="Corrected front text (only for rewrite)")
    back: str = Field(default="", description="Corrected back text (only for rewrite)")
    reason: str = Field(default="", description="Brief reason for the verdict")


class CritiqueOutput(BaseModel):
    reviews: list[CritiqueResult] = Field(description="Review results for each card")


# Stage F: Deduplication
class DedupResult(BaseModel):
    pair_index: int = Field(description="Index of the pair being reviewed (0-based)")
    action: str = Field(description="'keep_first', 'keep_second', 'keep_both', or 'merge'")
    merged_front: str = Field(default="", description="Merged front text (only for merge action)")
    merged_back: str = Field(default="", description="Merged back text (only for merge action)")


class DedupOutput(BaseModel):
    results: list[DedupResult] = Field(description="Dedup decisions for each pair")


def schema_for(model: type[BaseModel]) -> dict:
    """Convert a Pydantic model to a JSON Schema dict for tool_use."""
    return model.model_json_schema()
