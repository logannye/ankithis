"""Pipeline orchestrator: runs stages A→B→C→D→E→F→QC for a document."""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict, deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ankithis_api.models.card import Card
from ankithis_api.models.content_profile import ContentProfile
from ankithis_api.models.document import Document, Section
from ankithis_api.models.enums import (
    CardStyle,
    CardType,
    CritiqueVerdict,
    DeckSize,
    DocumentStatus,
    JobStatus,
)
from ankithis_api.models.generation import CardPlan, Concept, GenerationJob
from ankithis_api.services.parser import ParsedSection
from ankithis_api.services.qc import run_qc
from ankithis_api.services.section_annotator import annotate_section
from ankithis_api.services.stages.card_generation import generate_cards
from ankithis_api.services.stages.card_planning import plan_cards
from ankithis_api.services.stages.classification import classify_document
from ankithis_api.services.stages.concept_extraction import (  # noqa: F401 — extract_concepts kept for backward compat / tests
    extract_concepts,
    extract_concepts_batch,
)
from ankithis_api.services.stages.concept_merge import merge_concepts, merge_concepts_batch
from ankithis_api.services.stages.critique import apply_critique, critique_cards
from ankithis_api.services.stages.dedup import apply_dedup, find_duplicate_pairs, resolve_duplicates

logger = logging.getLogger(__name__)

STAGE_B_MAX_CONCEPTS_PER_BATCH = 30


async def run_pipeline(document_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession) -> None:
    """Run the full A→B→C→D→E→F→QC pipeline for a document."""
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
        # Stage 0: Content Classification
        await _update_job(db, job, JobStatus.CLASSIFYING)

        # Build ParsedSection list from DB sections for classification
        parsed_sections = []
        for section in doc.sections:
            paragraphs = [chunk.text for chunk in sorted(section.chunks, key=lambda c: c.position)]
            parsed_sections.append(
                ParsedSection(
                    title=section.title,
                    level=section.level or 1,
                    paragraphs=paragraphs,
                )
            )

        # Classify
        profile_dict = classify_document(parsed_sections)

        # Persist ContentProfile
        content_profile = ContentProfile(
            document_id=doc.id,
            content_type=profile_dict["content_type"],
            domain=profile_dict.get("domain", "general"),
            difficulty=profile_dict.get("difficulty", "intermediate"),
            information_density=profile_dict.get("information_density", "moderate"),
            structure_quality=profile_dict.get("structure_quality", "semi_structured"),
            primary_knowledge_type=profile_dict.get("primary_knowledge_type", "mixed"),
            recommended_cloze_ratio=profile_dict.get("recommended_cloze_ratio", 0.5),
            recommended_qa_ratio=profile_dict.get("recommended_qa_ratio", 0.5),
            special_considerations=profile_dict.get("special_considerations", []),
        )
        db.add(content_profile)

        # Annotate sections with pedagogical function
        for section in doc.sections:
            first_para = ""
            if section.chunks:
                sorted_chunks = sorted(section.chunks, key=lambda c: c.position)
                first_para = sorted_chunks[0].text[:500] if sorted_chunks else ""
            section.pedagogical_function = annotate_section(section.title, first_para)

        await db.flush()

        logger.info(
            "Stage 0 complete: type=%s domain=%s difficulty=%s",
            profile_dict["content_type"],
            profile_dict.get("domain"),
            profile_dict.get("difficulty"),
        )

        # Stage A: Concept Extraction (batched per section)
        await _update_job(db, job, JobStatus.STAGE_A)
        all_concepts_by_section: dict[uuid.UUID, list[dict]] = {}
        stage_a_batch_size = 4

        for section in doc.sections:
            chunks_list = sorted(section.chunks, key=lambda c: c.position)
            section_concepts: list[dict] = []
            for i in range(0, len(chunks_list), stage_a_batch_size):
                batch = chunks_list[i : i + stage_a_batch_size]
                batch_dicts = [{"text": c.text, "visual_context": c.visual_context} for c in batch]
                concepts = extract_concepts_batch(
                    batch_dicts,
                    study_goal=study_goal,
                    content_type=profile_dict.get("content_type"),
                    difficulty=profile_dict.get("difficulty"),
                    pedagogical_function=section.pedagogical_function,
                    knowledge_type=profile_dict.get("primary_knowledge_type"),
                )
                section_concepts.extend(concepts)
            all_concepts_by_section[section.id] = section_concepts

        # Stage B: Concept Merge (batched across small sections)
        await _update_job(db, job, JobStatus.STAGE_B)
        merged_concepts_all: list[dict] = []
        concept_to_section: dict[str, uuid.UUID] = {}
        content_type = profile_dict.get("content_type")

        # Group small sections into batches; large sections get their own call
        batch_buffer: list[tuple[str, list[dict], Section]] = []
        batch_concept_count = 0

        for section in doc.sections:
            raw_concepts = all_concepts_by_section.get(section.id, [])
            if not raw_concepts:
                continue

            if (
                len(raw_concepts) >= 10
                or batch_concept_count + len(raw_concepts) > STAGE_B_MAX_CONCEPTS_PER_BATCH
            ):
                # Flush current batch if any
                if batch_buffer:
                    _flush_merge_batch(
                        batch_buffer,
                        study_goal,
                        content_type,
                        doc,
                        db,
                        merged_concepts_all,
                        concept_to_section,
                    )
                    batch_buffer = []
                    batch_concept_count = 0

                if len(raw_concepts) >= 10:
                    # Large section gets its own call
                    merged = merge_concepts(
                        raw_concepts,
                        section.title,
                        study_goal,
                        content_type=content_type,
                    )
                    for c in merged:
                        concept_to_section[c["name"]] = section.id
                    merged_concepts_all.extend(merged)

                    # Persist concepts
                    for c in merged:
                        db.add(
                            Concept(
                                document_id=doc.id,
                                section_id=section.id,
                                name=c["name"],
                                description=c["description"],
                                importance=c["importance"],
                            )
                        )
                    continue

            batch_buffer.append((section.title, raw_concepts, section))
            batch_concept_count += len(raw_concepts)

        # Flush remaining batch
        if batch_buffer:
            _flush_merge_batch(
                batch_buffer,
                study_goal,
                content_type,
                doc,
                db,
                merged_concepts_all,
                concept_to_section,
            )

        await db.flush()

        # Stage C: Card Planning
        await _update_job(db, job, JobStatus.STAGE_C)
        total_words = sum(chunk.word_count for section in doc.sections for chunk in section.chunks)
        card_plans = plan_cards(
            merged_concepts_all,
            deck_size,
            card_style,
            study_goal,
            total_words,
            content_profile=profile_dict,
        )

        # Persist card plans
        concept_id_map = {}
        concepts_result = await db.execute(select(Concept).where(Concept.document_id == doc.id))
        for concept in concepts_result.scalars():
            concept_id_map[concept.name] = concept.id

        for plan in card_plans:
            concept_id = concept_id_map.get(plan["concept_name"])
            if concept_id:
                db.add(
                    CardPlan(
                        document_id=doc.id,
                        concept_id=concept_id,
                        card_type=plan["card_type"],
                        direction=plan["direction"],
                        priority=plan["priority"],
                        bloom_level=plan.get("bloom_level", "understand"),
                    )
                )

        await db.flush()

        # Stage D: Card Generation
        await _update_job(db, job, JobStatus.STAGE_D)

        source_text = "\n\n".join(
            chunk.text for section in doc.sections for chunk in section.chunks
        )

        # Build per-section text map so Stage D/E get relevant context per batch
        section_text_map: dict[str, str] = {}
        for section in doc.sections:
            section_text_map[str(section.id)] = "\n\n".join(
                chunk.text for chunk in sorted(section.chunks, key=lambda c: c.position)
            )

        concept_section_str = {k: str(v) for k, v in concept_to_section.items()}

        generated = generate_cards(
            card_plans,
            source_text,
            study_goal,
            content_profile=profile_dict,
            section_text_map=section_text_map,
            concept_to_section=concept_section_str,
        )

        # Stage E: Critique
        await _update_job(db, job, JobStatus.STAGE_E)
        reviews = critique_cards(
            generated,
            source_text,
            content_type=profile_dict.get("content_type"),
            section_text_map=section_text_map,
            concept_to_section=concept_section_str,
            plans=card_plans,
        )
        generated = apply_critique(generated, reviews)

        # Stage F: Dedup
        await _update_job(db, job, JobStatus.STAGE_F)
        dup_pairs = find_duplicate_pairs(generated)
        if dup_pairs:
            decisions = resolve_duplicates(generated, dup_pairs)
            generated = apply_dedup(generated, dup_pairs, decisions)

        # QC
        await _update_job(db, job, JobStatus.QC)
        generated = run_qc(generated)

        # Topological sort: prerequisites before dependents
        generated = _topological_sort_cards(generated, card_plans, merged_concepts_all)

        # Persist cards
        suppressed_count = 0
        for i, card_data in enumerate(generated):
            card_type = CardType.CLOZE if card_data["card_type"] == "cloze" else CardType.BASIC
            section_id = concept_to_section.get(_find_plan_concept(card_plans, i))
            is_suppressed = card_data.get("suppressed", False)
            if is_suppressed:
                suppressed_count += 1

            # Map critique verdict
            verdict_str = card_data.get("critique_verdict")
            critique_verdict = None
            if verdict_str:
                try:
                    critique_verdict = CritiqueVerdict(verdict_str)
                except ValueError:
                    pass

            db.add(
                Card(
                    document_id=doc.id,
                    section_id=section_id,
                    card_type=card_type,
                    front=card_data["front"],
                    back=card_data["back"],
                    tags=card_data.get("tags", ""),
                    critique_verdict=critique_verdict,
                    suppressed=is_suppressed,
                    sort_order=i,
                )
            )

        # Update document and job status
        doc.status = DocumentStatus.COMPLETED
        job.status = JobStatus.COMPLETED
        job.total_cards = len(generated)
        job.suppressed_cards = suppressed_count
        await db.commit()

    except Exception as e:
        logger.exception(f"Pipeline failed for document {document_id}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)[:1000]
        doc.status = DocumentStatus.FAILED
        await db.commit()
        raise


def _topological_sort_cards(
    generated: list[dict],
    card_plans: list[dict],
    concepts: list[dict],
) -> list[dict]:
    """Reorder generated cards so prerequisite concepts come before dependents.

    Cards for the same concept keep their original relative order.
    If cycles exist in the dependency graph, falls back to original order.
    """
    if not concepts or not generated:
        return generated

    # Build concept dependency graph from prerequisites
    all_concept_names: set[str] = set()
    graph: dict[str, set[str]] = defaultdict(set)  # concept -> set of prerequisites
    for c in concepts:
        name = c["name"]
        all_concept_names.add(name)
        for prereq in c.get("prerequisites", []):
            if prereq != name:  # ignore self-references
                graph[name].add(prereq)
                all_concept_names.add(prereq)

    # Kahn's algorithm for topological sort
    in_degree: dict[str, int] = {name: 0 for name in all_concept_names}
    adj: dict[str, list[str]] = defaultdict(list)  # prereq -> list of dependents
    for concept, prereqs in graph.items():
        for prereq in prereqs:
            adj[prereq].append(concept)
            in_degree[concept] = in_degree.get(concept, 0) + 1

    queue: deque[str] = deque(name for name in all_concept_names if in_degree.get(name, 0) == 0)
    sorted_names: list[str] = []
    while queue:
        node = queue.popleft()
        sorted_names.append(node)
        for dependent in adj.get(node, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # If cycle detected (not all nodes sorted), fall back to original order
    if len(sorted_names) < len(all_concept_names):
        logger.warning(
            "Cycle detected in concept prerequisites (%d/%d sorted), keeping original order",
            len(sorted_names),
            len(all_concept_names),
        )
        return generated

    # Build concept ordering map
    concept_order = {name: idx for idx, name in enumerate(sorted_names)}

    # Map each generated card to its concept name via card_plans
    def _card_concept(card_idx: int) -> str | None:
        if card_idx < len(card_plans):
            return card_plans[card_idx].get("concept_name")
        return None

    # Group cards by concept, preserving relative order within each concept
    concept_cards: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    orphans: list[tuple[int, dict]] = []
    for i, card in enumerate(generated):
        concept_name = _card_concept(i)
        if concept_name and concept_name in concept_order:
            concept_cards[concept_name].append((i, card))
        else:
            orphans.append((i, card))

    # Rebuild list: sorted concepts first, then orphans at the end
    result: list[dict] = []
    for concept_name in sorted_names:
        for _orig_idx, card in concept_cards.get(concept_name, []):
            result.append(card)
    for _orig_idx, card in orphans:
        result.append(card)

    return result


def _flush_merge_batch(
    batch_buffer: list[tuple[str, list[dict], Section]],
    study_goal: str,
    content_type: str | None,
    doc: Document,
    db: AsyncSession,
    merged_concepts_all: list[dict],
    concept_to_section: dict[str, uuid.UUID],
) -> None:
    """Merge a batch of small sections in a single LLM call and persist results."""
    sections_concepts = [(title, concepts) for title, concepts, _section in batch_buffer]

    if len(sections_concepts) == 1:
        # Single section — use the regular single-section call
        title, concepts, section = batch_buffer[0]
        merged = merge_concepts(
            concepts,
            title,
            study_goal,
            content_type=content_type,
        )
    else:
        merged = merge_concepts_batch(
            sections_concepts,
            study_goal=study_goal,
            content_type=content_type,
        )

    fallback_section = batch_buffer[0][2]

    for c in merged:
        # Try to match concept back to its originating section via merged_from
        assigned_section = fallback_section
        if len(batch_buffer) > 1:
            merged_from = set(c.get("merged_from", []))
            for title, concepts, section in batch_buffer:
                section_concept_names = {concept["name"] for concept in concepts}
                if merged_from & section_concept_names:
                    assigned_section = section
                    break

        concept_to_section[c["name"]] = assigned_section.id
        merged_concepts_all.append(c)

        db.add(
            Concept(
                document_id=doc.id,
                section_id=assigned_section.id,
                name=c["name"],
                description=c["description"],
                importance=c["importance"],
            )
        )


def _find_plan_concept(plans: list[dict], card_index: int) -> str | None:
    """Best-effort: map generated card index back to a plan's concept name."""
    if card_index < len(plans):
        return plans[card_index].get("concept_name")
    return None


async def _update_job(db: AsyncSession, job: GenerationJob, status: JobStatus) -> None:
    job.status = status
    job.current_stage = status.value
    await db.commit()
