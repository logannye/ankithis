"""Review endpoint: view generated cards grouped by section."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.auth import get_current_user
from ankithis_api.db import get_db
from ankithis_api.models.card import Card
from ankithis_api.models.document import Document, Section
from ankithis_api.models.enums import DocumentStatus
from ankithis_api.models.user import User

router = APIRouter()


class CardOut(BaseModel):
    id: str
    front: str
    back: str
    card_type: str
    tags: str | None
    critique_verdict: str | None
    suppressed: bool


class SectionCards(BaseModel):
    section_id: str
    section_title: str | None
    cards: list[CardOut]


class ReviewResponse(BaseModel):
    document_id: str
    title: str | None
    total_cards: int
    active_cards: int
    suppressed_cards: int
    sections: list[SectionCards]


@router.get("/api/documents/{document_id}/review", response_model=ReviewResponse)
async def review_cards(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Document generation not complete")

    # Get sections
    sections_result = await db.execute(
        select(Section).where(Section.document_id == document_id).order_by(Section.position)
    )
    sections = list(sections_result.scalars())

    # Get all cards
    cards_result = await db.execute(
        select(Card).where(Card.document_id == document_id).order_by(Card.sort_order)
    )
    all_cards = list(cards_result.scalars())

    # Group by section
    section_map: dict[uuid.UUID | None, list[Card]] = {}
    for card in all_cards:
        section_map.setdefault(card.section_id, []).append(card)

    section_groups = []
    for section in sections:
        cards = section_map.get(section.id, [])
        section_groups.append(
            SectionCards(
                section_id=str(section.id),
                section_title=section.title,
                cards=[
                    CardOut(
                        id=str(c.id),
                        front=c.front,
                        back=c.back,
                        card_type=c.card_type.value,
                        tags=c.tags,
                        critique_verdict=c.critique_verdict.value if c.critique_verdict else None,
                        suppressed=c.suppressed,
                    )
                    for c in cards
                ],
            )
        )

    # Cards without a section
    unsectioned = section_map.get(None, [])
    if unsectioned:
        section_groups.append(
            SectionCards(
                section_id="none",
                section_title="Unsectioned",
                cards=[
                    CardOut(
                        id=str(c.id),
                        front=c.front,
                        back=c.back,
                        card_type=c.card_type.value,
                        tags=c.tags,
                        critique_verdict=c.critique_verdict.value if c.critique_verdict else None,
                        suppressed=c.suppressed,
                    )
                    for c in unsectioned
                ],
            )
        )

    total = len(all_cards)
    suppressed = sum(1 for c in all_cards if c.suppressed)

    return ReviewResponse(
        document_id=str(doc.id),
        title=doc.title,
        total_cards=total,
        active_cards=total - suppressed,
        suppressed_cards=suppressed,
        sections=section_groups,
    )
