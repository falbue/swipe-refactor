from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from . import config
from sqlmodel import Session, select
from models import RefreshToken
import secrets
from user_agents import parse


def info_user_agent(user_agent: str) -> str:
    if not user_agent:
        return "Unknown Device"

    ua = parse(user_agent)

    # Пример формата: "Chrome on Windows", "Safari on iPhone", "Firefox on Ubuntu"
    browser = ua.browser.family or "Unknown Browser"
    os = ua.os.family or "Unknown OS"

    return f"{browser}/{os}"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=int(config.ACCESS_TOKEN_EXPIRE_MINUTES))
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


def verify_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return payload
    except JWTError:
        return None


def create_refresh_token(
    db: Session,
    user_id: int,
    device: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> RefreshToken:
    token_str = secrets.token_urlsafe(32)
    refresh_token = RefreshToken(
        token=token_str,
        user_id=user_id,
        device=device,
        ip_address=ip,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def get_valid_refresh_token(db: Session, token: str) -> RefreshToken | None:
    statement = select(RefreshToken).where(
        RefreshToken.token == token,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.now(timezone.utc),
    )
    return db.exec(statement).first()


def revoke_refresh_token(db: Session, token: str) -> bool:
    rt = db.exec(select(RefreshToken).where(RefreshToken.token == token)).first()
    if rt and rt.revoked_at is None:
        rt.revoked_at = datetime.now(timezone.utc)
        db.add(rt)
        db.commit()
        return True
    return False


def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> None:
    tokens = db.exec(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
    ).all()
    for token in tokens:
        token.revoked_at = datetime.now(timezone.utc)
    db.add_all(tokens)
    db.commit()
