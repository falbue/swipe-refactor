from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class SessionStatus(str, Enum):
    """Session status enum."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Session(SQLModel, table=True):
    """Session model for tracking code swipe sessions."""

    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    repo_full_name: str  # owner/repo
    base_commit_sha: str
    branch_name: str
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    total_cards: int = 0
    approved_cards: int = 0
    edited_cards: int = 0
    skipped_cards: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SessionResponse(SQLModel):
    """Session response model."""

    id: str
    repo_full_name: str
    status: SessionStatus
    total_cards: int
    approved_cards: int
    edited_cards: int
    skipped_cards: int
    created_at: datetime


class SessionCreateRequest(SQLModel):
    """Request model for session creation."""

    repo_full_name: str
