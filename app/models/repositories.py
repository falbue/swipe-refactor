from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, text
from enum import Enum


def utcnow():
    return datetime.now(timezone.utc)


class RepositoryStatus(str, Enum):
    active = "active"
    completed = "completed"
    abandoned = "abandoned"
    riddle = "riddle"


class Repository(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: Optional[int] = Field(foreign_key="user.id", default=None)
    is_public_template: bool = Field(default=True)
    repo_full_name: str = Field(nullable=False)  # owner/repo
    branch_name: str = Field(nullable=False)
    commit_name: str = Field(nullable=False)
    status: RepositoryStatus = Field(nullable=False)

    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )


class RepositoryCreate(SQLModel):
    repo_full_name: str


class RepositoryResponse(SQLModel):
    message: str
