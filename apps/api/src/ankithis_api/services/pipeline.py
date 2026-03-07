"""Pipeline orchestrator: runs stages A→B→C→D sequentially for a document."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ankithis_api.models.card import Card
from ankithis_api.models.document import Chunk, Document, Section
from ankithis_api.models.enums import CardStyle, CardType, DeckSize, DocumentStatus, JobStatus
from ankithis_api.models.generation import CardPlan, Concept, GenerationJob
from ankithis_api.services.stages.card_generation import generate_cards
from ankithis_api.services.stages.card_planning import plan_cards
from ankithis_api.services.stages.concept_extraction import extract_concepts
from ankithis_api.services.stages.concept_merge import merge_concepts

logger = logging.getLogger(__name__)


async def run_pipeline(document_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession) -> None:
    """Run the full A→B→C→D pipeline for a document."""
    # Load document with sections and chunks
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.sections).selectinload(Section.chunks))
        .options(selectinload(Document.options))
    )
    doc = result.scalar_one()
    job = await db.get(GenerationJob, job_id)

    study_goal = doc.options.study_goal if doc.options else "Master the key concepts"
    card_style = doc.options.card_style if doc.options else CardStyle.CLOZE_HEAVY
    deck_size = doc.options.deck_size if doc.options else DeckSize.MEDIUM

    try:
        # Stage A: Concept Extraction (per chunk)
        await _update_job(db, job, JobStatus.STAGE_A)
        all_concepts_by_section: dict[uuid.UUID, list[dict]] = {}

        for section in doc.sections:
            section_concepts = []
            for chunk in section.chunks:
                concepts = extract_concepts(chunk.text, study_goal)
                section_concepts.extend(concepts)
            all_concepts_by_section[section.id] = section_concepts

        # Stage B: Concept Merge (per section)
        await _update_job(db, job, JobStatus.STAGE_B)
        merged_concepts_all: list[dict] = []
        concept_to_section: dict[str, uuid.UUID] = {}

        for section in doc.sections:
            raw_concepts = all_concepts_by_section.get(section.id, [])
            if not raw_concepts:
                continue
            merged = merge_concepts(raw_concepts, section.title, study_goal)
            for c in merged:
                concept_to_section[c["name"]] = section.id
            merged_concepts_all.extend(merged)

            # Persist concepts
            for c in merged:
                db.add(Concept(
                    document_id=doc.id,
                    section_id=section.id,
                    name=c["name"],
                    description=c["description"],
                    importance=c["importance"],
                ))

        await db.flush()

        # Stage C: Card Planning
        await _update_job(db, job, JobStatus.STAGE_C)
        card_plans = plan_cards(merged_concepts_all, deck_size, card_style, study_goal)

        # Persist card plans (look up concept IDs)
        concept_id_map = {}
        concepts_result = await db.execute(
            select(Concept).where(Concept.document_id == doc.id)
        )
        for concept in concepts_result.scalars():
            concept_id_map[concept.name] = concept.id

        for plan in card_plans:
            concept_id = concept_id_map.get(plan["concept_name"])
            if concept_id:
                db.add(CardPlan(
                    document_id=doc.id,
                    concept_id=concept_id,
                    card_type=plan["card_type"],
                    direction=plan["direction"],
                    priority=plan["priority"],
                ))

        await db.flush()

        # Stage D: Card Generation
        await _update_job(db, job, JobStatus.STAGE_D)

        # Gather source text for context
        source_text = "\n\n".join(
            chunk.text
            for section in doc.sections
            for chunk in section.chunks
        )

        generated = generate_cards(card_plans, source_text, study_goal)

        # Persist cards
        for i, card_data in enumerate(generated):
            card_type = CardType.CLOZE if card_data["card_type"] == "cloze" else CardType.BASIC
            # Try to map back to section via concept
            section_id = concept_to_section.get(
                _find_plan_concept(card_plans, i)
            )
            db.add(Card(
                document_id=doc.id,
                section_id=section_id,
                card_type=card_type,
                front=card_data["front"],
                back=card_data["back"],
                tags=card_data.get("tags", ""),
                sort_order=i,
            ))

        # Update document and job status
        doc.status = DocumentStatus.COMPLETED
        job.status = JobStatus.COMPLETED
        job.total_cards = len(generated)
        await db.commit()

    except Exception as e:
        logger.exception(f"Pipeline failed for document {document_id}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)[:1000]
        doc.status = DocumentStatus.FAILED
        await db.commit()
        raise


def _find_plan_concept(plans: list[dict], card_index: int) -> str | None:
    """Best-effort: map generated card index back to a plan's concept name."""
    if card_index < len(plans):
        return plans[card_index].get("concept_name")
    return None


async def _update_job(db: AsyncSession, job: GenerationJob, status: JobStatus) -> None:
    job.status = status
    job.current_stage = status.value
    await db.commit()
