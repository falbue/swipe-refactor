from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class CardStatus(str, Enum):
    """Card status enum."""

    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    SKIPPED = "skipped"
    NEEDS_REVIEW = "needs_review"


class Card(SQLModel, table=True):
    """Card model for code swipe cards."""

    id: Optional[str] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="session.id")
    card_hash: str = Field(unique=True, index=True)
    file_path: str
    start_line: int
    end_line: int
    ast_signature: str  # Function signature
    content_hash: str
    original_content: str
    edited_content: Optional[str] = None
    status: CardStatus = Field(default=CardStatus.PENDING)
    is_public: bool = False
    gist_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CardResponse(SQLModel):
    """Card response model."""

    id: str
    file_path: str
    start_line: int
    end_line: int
    ast_signature: str
    original_content: str
    status: CardStatus
    is_public: bool


class CardCreateRequest(SQLModel):
    """Request model for card creation."""

    file_path: str
    start_line: int
    end_line: int
    ast_signature: str
    content: str
