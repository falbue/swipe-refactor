from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship, text
from typing import Optional
from datetime import datetime, timezone
from enum import Enum as PyEnum


def utcnow():
    return datetime.now(timezone.utc)


class RepositoryStatus(str, PyEnum):
    active = "active"
    completed = "completed"
    abandoned = "abandoned"
    riddle = "riddle"


class CardSeverity(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CardStatus(str, PyEnum):
    approved = "approved"
    edited = "edited"
    skipped = "skipped"
    needs_review = "needs_review"
    deleted = "deleted"


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    github_id: str = Field(unique=True, nullable=False, max_length=100)
    access_token: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )


class Repository(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: Optional[int] = Field(foreign_key="user.id", default=None)
    is_public_template: bool = Field(default=True)
    repo_full_name: str = Field(nullable=False)  # owner/repo
    branch_name: str = Field(nullable=False)
    commit_name: str = Field(nullable=False)
    status: RepositoryStatus = Field(nullable=False)

    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )


class Card(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    repository_id: UUID = Field(foreign_key="repository.id", nullable=False)
    file_path: str = Field(nullable=False)
    kind: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    ast_hash: bytes = Field(nullable=True)  # BLOB → bytes
    error_message: str = Field(nullable=True)
    severity: CardSeverity = Field(nullable=False)
    status: CardStatus = Field(nullable=False)
    is_public: bool = Field(default=False)
    gist_url: str = Field(nullable=True)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP"),
        },
    )


class CardLike(SQLModel, table=True):
    __tablename__ = "card_like"

    id: int = Field(default=None, primary_key=True)
    card_id: UUID = Field(foreign_key="card.id", nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    liked_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    token: str = Field(unique=True, max_length=255, index=True, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    device: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=512)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)
    revoked_at: Optional[datetime] = None
