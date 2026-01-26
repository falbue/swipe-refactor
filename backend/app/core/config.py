from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./swipe.db"
    echo_sql: bool = False

    # Server
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    debug: bool = True

    # GitHub OAuth
    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str = "http://localhost:8000/auth/github/callback"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Session
    session_timeout_hours: int = 24

    # Git
    repos_work_dir: str = "./repos"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
