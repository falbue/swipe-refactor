from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.card import Card, CardResponse, CardStatus
from app.models.session import Session as SessionModel
from datetime import datetime
from pydantic import BaseModel


class EditCardRequest(BaseModel):
    """Request model for editing a card."""

    edited_content: str


router = APIRouter(prefix="/api/cards", tags=["cards"])


@router.post("/{card_id}/approve")
async def approve_card(
    card_id: str,
    session: Session = Depends(get_session),
):
    """Approve a card (swipe right)."""
    card = session.exec(select(Card).where(Card.id == card_id)).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.status = CardStatus.APPROVED
    card.updated_at = datetime.utcnow()
    session.add(card)

    # Update session stats
    db_session = session.exec(
        select(SessionModel).where(SessionModel.id == card.session_id)
    ).first()
    if db_session:
        db_session.approved_cards += 1
        db_session.updated_at = datetime.utcnow()
        session.add(db_session)

    session.commit()

    return {"status": "approved", "card_id": card_id}


@router.post("/{card_id}/edit")
async def edit_card(
    card_id: str,
    body: EditCardRequest,
    session: Session = Depends(get_session),
):
    """Edit a card (swipe left)."""
    card = session.exec(select(Card).where(Card.id == card_id)).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if not body.edited_content.strip():
        raise HTTPException(status_code=400, detail="Edited content cannot be empty")

    card.edited_content = body.edited_content
    card.status = CardStatus.EDITED
    card.updated_at = datetime.utcnow()
    session.add(card)

    # Update session stats
    db_session = session.exec(
        select(SessionModel).where(SessionModel.id == card.session_id)
    ).first()
    if db_session:
        db_session.edited_cards += 1
        db_session.updated_at = datetime.utcnow()
        session.add(db_session)

    session.commit()

    # TODO: Make local git commit with changes

    return {"status": "edited", "card_id": card_id}


@router.post("/{card_id}/skip")
async def skip_card(
    card_id: str,
    session: Session = Depends(get_session),
):
    """Skip a card."""
    card = session.exec(select(Card).where(Card.id == card_id)).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    card.status = CardStatus.SKIPPED
    card.updated_at = datetime.utcnow()
    session.add(card)

    # Update session stats
    db_session = session.exec(
        select(SessionModel).where(SessionModel.id == card.session_id)
    ).first()
    if db_session:
        db_session.skipped_cards += 1
        db_session.updated_at = datetime.utcnow()
        session.add(db_session)

    session.commit()

    return {"status": "skipped", "card_id": card_id}
