from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlmodel import Column, Field, SQLModel, text
from enum import Enum as PyEnum
from sqlalchemy.dialects.postgresql import BYTEA


def utcnow():
    return datetime.now(timezone.utc)


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


class CardBase(SQLModel):
    repository_id: UUID = Field(foreign_key="repository.id", nullable=False)
    file_path: str = Field(nullable=False)
    kind: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    error_message: str = Field(nullable=True)
    severity: CardSeverity = Field(nullable=False)
    status: CardStatus = Field(nullable=False)
    is_public: bool = Field(default=False)
    gist_url: str = Field(nullable=True)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    update_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP"),
        },
    )


class Card(CardBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ast_hash: bytes = Field(default=None, sa_column=Column(BYTEA, nullable=True))


class CardResponse(CardBase):
    id: UUID


class CardCodeRequest(SQLModel):
    repository_id: UUID
    file_path: str
    kind: str
    full_name: str


class CardCodeResponse(CardBase):
    start_line: int
    end_line: int
    code: str
