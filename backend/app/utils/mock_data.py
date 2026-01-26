"""Mock data and utilities for code analysis (MVP)."""

import hashlib
from typing import List
from uuid import uuid4
from app.models.card import Card
from sqlmodel import Session


MOCK_CARDS_DATA = [
    {
        "file_path": "src/utils.py",
        "start_line": 1,
        "end_line": 15,
        "ast_signature": "def validate_email(email: str) -> bool",
        "original_content": '''def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    else:
        return False''',
    },
    {
        "file_path": "src/database.py",
        "start_line": 42,
        "end_line": 58,
        "ast_signature": "def get_user_by_id(user_id: int) -> Optional[User]",
        "original_content": '''def get_user_by_id(user_id: int) -> Optional[User]:
    """Fetch user from database by ID."""
    try:
        result = db.query(User).filter(User.id == user_id)
        if result:
            return result
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None''',
    },
    {
        "file_path": "src/api/handlers.py",
        "start_line": 89,
        "end_line": 110,
        "ast_signature": "def process_data(data: dict) -> dict",
        "original_content": '''def process_data(data: dict) -> dict:
    """Process incoming data."""
    result = {}
    for key in data:
        if key == 'name':
            result['name'] = data[key].strip().lower()
        elif key == 'age':
            if data[key] > 0:
                result['age'] = data[key]
        elif key == 'email':
            result['email'] = data[key]
    return result''',
    },
    {
        "file_path": "src/parser.py",
        "start_line": 125,
        "end_line": 145,
        "ast_signature": "def parse_json(content: str) -> dict",
        "original_content": '''def parse_json(content: str) -> dict:
    """Parse JSON string to dict."""
    import json
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        return {}
    except Exception as e:
        print(str(e))
        return {}''',
    },
    {
        "file_path": "src/logger.py",
        "start_line": 7,
        "end_line": 22,
        "ast_signature": "def log_message(message: str, level: str = 'info') -> None",
        "original_content": '''def log_message(message: str, level: str = 'info') -> None:
    """Log a message with timestamp."""
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if level == 'info':
        print(f"[INFO] {timestamp}: {message}")
    elif level == 'error':
        print(f"[ERROR] {timestamp}: {message}")
    elif level == 'warning':
        print(f"[WARNING] {timestamp}: {message}")''',
    },
]


def generate_card_hash(file_path: str, ast_signature: str, content: str) -> str:
    """Generate unique hash for a card."""
    combined = f"{file_path}:{ast_signature}:{content}"
    return hashlib.sha256(combined.encode()).hexdigest()


def create_mock_cards(session_id: str, db_session: Session) -> int:
    """Create mock cards for testing (MVP)."""
    created_count = 0

    for card_data in MOCK_CARDS_DATA:
        card_hash = generate_card_hash(
            card_data["file_path"],
            card_data["ast_signature"],
            card_data["original_content"],
        )

        # Check if card already exists
        from sqlmodel import select
        from app.models.card import Card

        existing = db_session.exec(
            select(Card).where(Card.card_hash == card_hash)
        ).first()

        if not existing:
            card = Card(
                id=str(uuid4()),
                session_id=session_id,
                card_hash=card_hash,
                file_path=card_data["file_path"],
                start_line=card_data["start_line"],
                end_line=card_data["end_line"],
                ast_signature=card_data["ast_signature"],
                content_hash=generate_card_hash(
                    card_data["file_path"],
                    card_data["ast_signature"],
                    card_data["original_content"],
                ),
                original_content=card_data["original_content"],
            )
            db_session.add(card)
            created_count += 1

    db_session.commit()
    return created_count
