"""Section management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.auth import get_current_user
from ankithis_api.db import get_db
from ankithis_api.models.card import Card
from ankithis_api.models.document import Document, Section
from ankithis_api.models.user import User

router = APIRouter()


class SectionRemoveResponse(BaseModel):
    section_id: str
    cards_suppressed: int


@router.post("/api/sections/{section_id}/remove-from-deck", response_model=SectionRemoveResponse)
async def remove_section_from_deck(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Verify ownership through document
    doc_result = await db.execute(
        select(Document).where(Document.id == section.document_id, Document.user_id == user.id)
    )
    if not doc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Section not found")

    # Suppress all cards in this section
    stmt = (
        update(Card)
        .where(Card.section_id == section_id, Card.suppressed == False)  # noqa: E712
        .values(suppressed=True)
    )
    result = await db.execute(stmt)
    cards_suppressed = result.rowcount

    section.excluded = True
    await db.commit()

    return SectionRemoveResponse(
        section_id=str(section.id),
        cards_suppressed=cards_suppressed,
    )
