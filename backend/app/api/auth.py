from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.database import get_session
from app.models.user import User, UserResponse
from datetime import datetime


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/github/callback")
async def github_callback(
    code: str,
    state: str,
    session: Session = Depends(get_session),
) -> UserResponse:
    """GitHub OAuth callback endpoint."""
    # TODO: Implement GitHub OAuth token exchange
    # For now, return mock data
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me", response_model=UserResponse)
async def get_me(session: Session = Depends(get_session)) -> UserResponse:
    """Get current user info."""
    # TODO: Implement JWT token verification
    raise HTTPException(status_code=401, detail="Not authenticated")
