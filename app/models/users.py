from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel, text


def utcnow():
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    github_id: str = Field(unique=True, nullable=False, max_length=100)
    access_token: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
