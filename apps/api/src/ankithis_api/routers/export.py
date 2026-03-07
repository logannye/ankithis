"""Export endpoints: download generated cards as CSV or APKG."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.db import get_db
from ankithis_api.models.card import Card
from ankithis_api.models.document import Document
from ankithis_api.models.enums import DocumentStatus
from ankithis_api.services.exporter import export_apkg, export_csv

router = APIRouter()


async def _get_active_cards(document_id: uuid.UUID, db: AsyncSession) -> tuple[Document, list[dict]]:
    """Fetch document and its non-suppressed cards."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != DocumentStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Document generation not complete")

    cards_result = await db.execute(
        select(Card)
        .where(Card.document_id == document_id, Card.suppressed == False)  # noqa: E712
        .order_by(Card.sort_order)
    )
    cards = [
        {
            "front": c.front,
            "back": c.back,
            "card_type": c.card_type.value,
            "tags": c.tags or "",
        }
        for c in cards_result.scalars()
    ]
    return doc, cards


@router.get("/api/documents/{document_id}/export/csv")
async def export_csv_endpoint(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    doc, cards = await _get_active_cards(document_id, db)
    csv_bytes = export_csv(cards)
    filename = f"{doc.title or 'ankithis'}_cards.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/documents/{document_id}/export/apkg")
async def export_apkg_endpoint(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    doc, cards = await _get_active_cards(document_id, db)
    deck_name = doc.title or "AnkiThis Deck"
    apkg_bytes = export_apkg(cards, deck_name)
    filename = f"{doc.title or 'ankithis'}_deck.apkg"
    return Response(
        content=apkg_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
