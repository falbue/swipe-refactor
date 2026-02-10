from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select
from core.parsers import scanner
from models.cards import Card, CardCodeResponse, CardResponse
from db.session import get_db


router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/", response_model=list[CardResponse])
def get_cards(db: Session = Depends(get_db)):
    cards = db.exec(select(Card)).all()
    if not cards:
        http_exception = HTTPException(status_code=400, detail="Карточки не найдены")
        raise http_exception
    return cards


@router.get("/{card_id}", response_model=CardCodeResponse)
def get_card(card_id: UUID, db: Session = Depends(get_db)):
    card = db.exec(select(Card).where(Card.id == card_id)).first()
    if not card:
        http_exception = HTTPException(
            status_code=404,
            detail=f"Карточка {card_id} не найдена",
        )
        raise http_exception
    code = scanner.get_code(db, card_id)
    response_data = {**card.dict(), **code}  # type: ignore
    return CardCodeResponse(**response_data)


@router.get("/repo/{repo_id}/random", response_model=CardResponse)
def get_random_card_from_repo(repo_id: UUID, db: Session = Depends(get_db)):
    card = db.exec(
        select(Card).where(Card.repository_id == repo_id).order_by(func.random())
    ).first()
    if not card:
        http_exception = HTTPException(
            status_code=404,
            detail=f"Карточки для репозитория {repo_id} не найдены",
        )
        raise http_exception
    return card
