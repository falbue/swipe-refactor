import os
import fnmatch
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import Depends
from sqlmodel import Session, select

from core.config import config
from db.session import get_db
from models.cards import Card, CardSeverity, CardStatus
from models.repositories import Repository
from .python_parser import extract_python_entities

# Поддерживаемые расширения
EXTENSIONS = {
    ".py": extract_python_entities,
}


def _resolve_repository(
    repo_path: str, repository_id: Optional[UUID], db: Session
) -> Repository:
    """Определяет Repository по repository_id или по пути к репозиторию"""
    if repository_id:
        repo = db.exec(select(Repository).where(Repository.id == repository_id)).first()
        if not repo:
            raise ValueError(f"Repository не найден по id: {repository_id}")
        return repo

    repo_path_abs = os.path.abspath(os.path.normpath(repo_path))
    temp_root = os.path.abspath(os.path.normpath(config.TEMP_REPO_PATH))

    try:
        rel_path = os.path.relpath(repo_path_abs, temp_root)
    except ValueError:
        rel_path = ""

    parts = Path(rel_path).parts
    if len(parts) >= 2:
        repo_full_name = f"{parts[0]}/{parts[1]}"
        repo = db.exec(
            select(Repository).where(Repository.repo_full_name == repo_full_name)
        ).first()
        if repo:
            return repo

    raise ValueError(
        "Не удалось определить repository_id. "
        "Передайте repository_id явно или убедитесь, что путь лежит в TEMP_REPO_PATH."
    )


def _get_session(db):
    if isinstance(db, Session):
        return db, None
    gen = get_db()
    return next(gen), gen


def scan_repo(
    repo_path: str, repository_id: Optional[UUID] = None, db: Session = Depends(get_db)
):
    repo_path = os.path.abspath(os.path.normpath(repo_path))
    if not os.path.isdir(repo_path):
        raise ValueError(f"Это не папка: {repo_path}")

    IGNORE_PATTERNS = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        "build",
        "dist",
        ".tox",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.so",
        "*.dll",
        "*.exe",
        "Thumbs.db",
        ".DS_Store",
    }

    def should_ignore(path: str) -> bool:
        name = os.path.basename(path)
        for pattern in IGNORE_PATTERNS:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    db_session, db_gen = _get_session(db)
    try:
        repo = _resolve_repository(repo_path, repository_id, db_session)
        db_session.commit()
        # Рекурсивный обход
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
            for file in files:
                if should_ignore(file):
                    continue
                ext = Path(file).suffix.lower()
                if ext not in EXTENSIONS:
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                print(f"Сканирование: {rel_path}")
                try:
                    extractor = EXTENSIONS[ext]
                    entities = extractor(file_path)
                except Exception as e:
                    print(f"  ❌ Ошибка при разборе {rel_path}: {e}")
                    continue
                # Разрешаем дубли имён в рамках одного файла
                seen_names = {}
                final_entities = []
                for ent in entities:
                    name = ent["full_name"]
                    if name in seen_names:
                        seen_names[name] += 1
                        new_name = f"{name}#{seen_names[name]}"
                        ent = ent.copy()
                        ent["full_name"] = new_name
                        error_msg = "⚠️ Дублирующееся имя функции/класса в этом файле"
                    else:
                        seen_names[name] = 1
                        error_msg = "TODO: implement analysis"
                    final_entities.append({**ent, "error_message": error_msg})
                # Сохраняем все сущности
                for ent in final_entities:
                    db_session.add(
                        Card(
                            repository_id=repo.id,
                            file_path=rel_path,
                            kind=ent["kind"],
                            full_name=ent["full_name"],
                            ast_hash=ent.get("ast_hash"),
                            error_message=ent["error_message"],
                            severity=CardSeverity.medium,
                            status=CardStatus.needs_review,
                            is_public=False,
                            gist_url="",
                        )
                    )
        db_session.commit()
    finally:
        if db_gen:
            try:
                next(db_gen)
            except StopIteration:
                pass

    print(f"\n✅ Сканирование завершено. Репозиторий: {repo_path}")
