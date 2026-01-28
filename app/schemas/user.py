from datetime import datetime
from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    email: str = Field(
        ...,
        max_length=128,
        title="Email пользователя",
        description="Email должен быть уникальным",
    )
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(SQLModel):
    id: int
    email: str
    role: str
    created_at: datetime
    access_token: str

    class Config:
        from_attributes = True
