from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from app.core.database import get_session
from app.models.session import (
    SessionResponse,
    SessionCreateRequest,
    Session as SessionModel,
    SessionStatus,
)
from app.models.card import Card, CardResponse, CardStatus
from app.utils.mock_data import create_mock_cards
from uuid import uuid4
from datetime import datetime
import random


router = APIRouter(prefix="/api/session", tags=["sessions"])


@router.post("/", response_model=SessionResponse)
async def create_session(
    body: SessionCreateRequest,
    session: Session = Depends(get_session),
) -> SessionResponse:
    """Create a new swipe session."""
    session_id = str(uuid4())

    new_session = SessionModel(
        id=session_id,
        user_id=1,  # TODO: Get from JWT token
        repo_full_name=body.repo_full_name,
        base_commit_sha="",
        branch_name=f"code-swipe/session-{session_id}",
        status=SessionStatus.ACTIVE,
    )
    session.add(new_session)
    session.commit()
    session.refresh(new_session)

    # Create mock cards for MVP
    cards_created = create_mock_cards(session_id, session)
    new_session.total_cards = cards_created
    session.add(new_session)
    session.commit()
    session.refresh(new_session)

    return SessionResponse(
        id=new_session.id,
        repo_full_name=new_session.repo_full_name,
        status=new_session.status,
        total_cards=new_session.total_cards,
        approved_cards=new_session.approved_cards,
        edited_cards=new_session.edited_cards,
        skipped_cards=new_session.skipped_cards,
        created_at=new_session.created_at,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_info(
    session_id: str,
    session: Session = Depends(get_session),
) -> SessionResponse:
    """Get session information."""
    db_session = session.exec(
        select(SessionModel).where(SessionModel.id == session_id)
    ).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=db_session.id,
        repo_full_name=db_session.repo_full_name,
        status=db_session.status,
        total_cards=db_session.total_cards,
        approved_cards=db_session.approved_cards,
        edited_cards=db_session.edited_cards,
        skipped_cards=db_session.skipped_cards,
        created_at=db_session.created_at,
    )


@router.get("/{session_id}/cards/random", response_model=CardResponse)
async def get_random_card(
    session_id: str,
    session: Session = Depends(get_session),
) -> CardResponse:
    """Get next random card for swipe."""
    # Verify session exists
    db_session_obj = session.exec(
        select(SessionModel).where(SessionModel.id == session_id)
    ).first()
    if not db_session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    # Debug: Get all cards for this session
    all_cards = session.exec(select(Card).where(Card.session_id == session_id)).all()
    print(f"DEBUG: Total cards for session {session_id}: {len(all_cards)}")
    for card in all_cards:
        print(f"  - Card {card.id}: status={card.status}, file={card.file_path}")

    # Get pending cards
    pending_cards = session.exec(
        select(Card)
        .where(Card.session_id == session_id)
        .where(Card.status == CardStatus.PENDING)
    ).all()

    print(f"DEBUG: Pending cards: {len(pending_cards)}")

    if not pending_cards:
        raise HTTPException(status_code=404, detail="No more cards to process")

    # Return random pending card
    card = random.choice(pending_cards)
    return CardResponse(
        id=card.id,
        file_path=card.file_path,
        start_line=card.start_line,
        end_line=card.end_line,
        ast_signature=card.ast_signature,
        original_content=card.original_content,
        status=card.status,
        is_public=card.is_public,
    )


@router.post("/{session_id}/create-pr")
async def create_pull_request(
    session_id: str,
    session: Session = Depends(get_session),
):
    """Create pull request from session branch."""
    db_session = session.exec(
        select(SessionModel).where(SessionModel.id == session_id)
    ).first()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get edited cards count
    edited_count = session.exec(
        select(func.count(Card.id))
        .where(Card.session_id == session_id)
        .where(Card.status == CardStatus.EDITED)
    ).first()

    if not edited_count or edited_count == 0:
        raise HTTPException(status_code=400, detail="No edited cards to create PR from")

    # Update session status
    db_session.status = SessionStatus.COMPLETED
    db_session.updated_at = datetime.utcnow()
    session.add(db_session)
    session.commit()

    # TODO: Implement actual GitHub PR creation with GitPython
    # For now, return mock response
    return {
        "status": "success",
        "message": f"Pull request created with {edited_count} changes",
        "branch": db_session.branch_name,
        "edited_cards": edited_count,
        "pr_url": f"https://github.com/{db_session.repo_full_name}/pulls",  # Mock URL
    }
