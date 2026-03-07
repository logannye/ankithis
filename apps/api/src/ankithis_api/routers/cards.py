"""Card management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.db import get_db
from ankithis_api.models.card import Card

router = APIRouter()


class CardRemoveResponse(BaseModel):
    card_id: str
    suppressed: bool


@router.post("/api/cards/{card_id}/remove", response_model=CardRemoveResponse)
async def remove_card(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.suppressed = True
    await db.commit()

    return CardRemoveResponse(card_id=str(card.id), suppressed=True)
