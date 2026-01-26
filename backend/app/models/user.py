from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class User(SQLModel, table=True):
    """User model for GitHub OAuth authentication."""

    id: Optional[int] = Field(default=None, primary_key=True)
    github_id: int = Field(unique=True, index=True)
    github_username: str = Field(index=True)
    access_token: str
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserResponse(SQLModel):
    """User response model (without sensitive data)."""

    id: int
    github_username: str
    avatar_url: Optional[str]
    email: Optional[str]
