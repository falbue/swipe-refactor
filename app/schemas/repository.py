from datetime import datetime
from sqlmodel import Field, SQLModel


class RepositoryCreate(SQLModel):
    repo_full_name: str


class RepositoryResponse(SQLModel):
    message: str

    class Config:
        from_attributes = True
