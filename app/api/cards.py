import os
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.config import config
from core.parsers.python_parser import find_python_entity_block
from models.cards import Card, CardCodeRequest, CardCodeResponse, CardResponse
from models.repositories import Repository
from db.session import get_db


router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/{repo_id}", response_model=list[CardResponse])
def get_cards(repo_id: UUID, db: Session = Depends(get_db)):
    cards = db.exec(select(Card).where(Card.repository_id == repo_id)).all()
    if not cards:
        http_exception = HTTPException(
            status_code=404, detail=f"Карточки репозитория {repo_id} не найдены"
        )
        raise http_exception
    return cards


@router.get("/{repo_id}/{card_id}", response_model=CardResponse)
def get_card(repo_id: UUID, card_id: UUID, db: Session = Depends(get_db)):
    card = db.exec(
        select(Card).where(Card.repository_id == repo_id, Card.id == card_id)
    ).first()
    if not card:
        http_exception = HTTPException(
            status_code=404,
            detail=f"Карточка {card_id} репозитория {repo_id} не найдена",
        )
        raise http_exception
    return card


@router.post("/code", response_model=CardCodeResponse)
def get_card_code(payload: CardCodeRequest, db: Session = Depends(get_db)):
    repo = db.exec(
        select(Repository).where(Repository.id == payload.repository_id)
    ).first()
    if not repo:
        raise HTTPException(
            status_code=404,
            detail=f"Репозиторий {payload.repository_id} не найден",
        )

    repo_root = os.path.abspath(
        os.path.join(config.TEMP_REPO_PATH, repo.repo_full_name)
    )
    requested_path = os.path.abspath(os.path.join(repo_root, payload.file_path))
    if not requested_path.startswith(repo_root + os.sep):
        raise HTTPException(status_code=400, detail="Некорректный путь к файлу")
    if not os.path.isfile(requested_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    if Path(requested_path).suffix.lower() != ".py":
        raise HTTPException(status_code=400, detail="Поддерживаются только .py файлы")

    try:
        block = find_python_entity_block(
            requested_path, payload.kind, payload.full_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return CardCodeResponse(
        file_path=payload.file_path,
        kind=block["kind"],
        full_name=block["full_name"],
        start_line=block["start_line"],
        end_line=block["end_line"],
        code=block["code"],
    )
