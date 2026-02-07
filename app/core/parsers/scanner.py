import os
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

from fastapi import Depends
from sqlmodel import Session, col, select
from typing import Set, Tuple

from core.config import config
from db.session import get_db
from models.cards import Card, CardSeverity, CardStatus
from models.repositories import Repository
from .python_parser import extract_python_entities, find_python_entity_block

# Поддерживаемые расширения
EXTENSIONS = {
    ".py": extract_python_entities,
}


def get_code(db: Session, card_id: UUID):
    # Шаг 1: Получаем карточку по ID
    card = db.get(Card, card_id)
    if not card:
        return f"Карточка с id={card_id} не найдена"

    # Шаг 2: Получаем репозиторий
    repo = db.exec(
        select(Repository).where(Repository.id == card.repository_id)
    ).first()
    if not repo:
        return f"Репозиторий с id={card.repository_id} не найден"

    # Шаг 3: Формируем путь к файлу
    repo_root = os.path.abspath(
        os.path.join(config.TEMP_REPO_PATH, repo.repo_full_name)
    )
    requested_path = os.path.abspath(os.path.join(repo_root, card.file_path))

    # Защита от path traversal
    if not requested_path.startswith(repo_root + os.sep):
        return "Некорректный путь к файлу"

    if not os.path.isfile(requested_path):
        return "Файл не найден"

    if Path(requested_path).suffix.lower() != ".py":
        return "Поддерживаются только .py файлы"

    # Шаг 4: Извлекаем блок кода
    try:
        block = find_python_entity_block(requested_path, card.kind, card.full_name)
    except ValueError as exc:
        return str(exc)

    # Шаг 5: Возвращаем ответ
    return {
        "start_line": block["start_line"],
        "end_line": block["end_line"],
        "code": block["code"],
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
    repo_path: str,
    repository_id: Optional[UUID] = None,
    db: Session = Depends(get_db),  # если вызывается как зависимость FastAPI
):
    repo_path = os.path.abspath(os.path.normpath(repo_path))
    if not os.path.isdir(repo_path):
        raise ValueError(f"Это не папка: {repo_path}")

    # Только папки и точные имена файлов для пропуска при os.walk
    IGNORE_NAMES = {
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
        "Thumbs.db",
        ".DS_Store",
    }

    def should_ignore(path: str) -> bool:
        return os.path.basename(path) in IGNORE_NAMES

    db_session, db_gen = _get_session(db)
    try:
        repo = _resolve_repository(repo_path, repository_id, db_session)
        db_session.commit()

        # 🔹 Шаг 1: Загрузить все существующие карточки для этого репозитория
        existing_cards = db_session.exec(
            select(Card).where(Card.repository_id == repo.id)
        ).all()
        existing_key_to_card: Dict[Tuple[str, str], Card] = {
            (card.file_path, card.full_name): card for card in existing_cards
        }
        existing_keys: Set[Tuple[str, str]] = set(existing_key_to_card.keys())

        # 🔹 Шаг 2: Собрать новые сущности из файлов
        new_key_to_entity: Dict[Tuple[str, str], dict] = {}

        for root, dirs, files in os.walk(repo_path):
            # Модифицируем dirs in-place — os.walk это поддерживает
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in EXTENSIONS:
                    continue  # пропускаем неподдерживаемые расширения

                file_path_abs = os.path.join(root, file)
                rel_path = os.path.relpath(file_path_abs, repo_path)

                print(f"Сканирование: {rel_path}")
                try:
                    extractor = EXTENSIONS[ext]
                    entities = extractor(file_path_abs)
                except Exception as e:
                    print(f"  ❌ Ошибка при разборе {rel_path}: {e}")
                    continue

                # Обработка дубликатов имён в рамках одного файла
                seen_names = {}
                final_entities = []
                for ent in entities:
                    name = ent["full_name"]
                    if name in seen_names:
                        seen_names[name] += 1
                        new_name = f"{name}#{seen_names[name]}"
                        ent = ent.copy()
                        ent["full_name"] = new_name
                    else:
                        seen_names[name] = 1
                    final_entities.append(ent)

                for ent in final_entities:
                    key = (rel_path, ent["full_name"])
                    new_key_to_entity[key] = ent

        # 🔹 Шаг 3: Синхронизация — обновление и вставка
        new_keys: Set[Tuple[str, str]] = set(new_key_to_entity.keys())

        for key in new_keys:
            ent = new_key_to_entity[key]
            ast_hash_new = ent["ast_hash"]
            error_msg = "TODO: implement analysis"

            if key in existing_key_to_card:
                # Существующая запись — проверяем хэш
                card = existing_key_to_card[key]
                if card.ast_hash != ast_hash_new:
                    # Обновляем только если хэш изменился
                    card.ast_hash = ast_hash_new
                    card.error_message = error_msg
                    # Можно обновить другие поля, если нужно
                    db_session.add(card)
            else:
                # Новая сущность — создаём
                db_session.add(
                    Card(
                        repository_id=repo.id,
                        file_path=key[0],
                        kind=ent["kind"],
                        full_name=key[1],
                        ast_hash=ast_hash_new,
                        error_message=error_msg,
                        severity=CardSeverity.medium,
                        status=CardStatus.needs_review,
                        is_public=False,
                        gist_url="",
                    )
                )

        # 🔹 Шаг 4: Удаление устаревших (которых больше нет в коде)
        keys_to_delete = existing_keys - new_keys
        if keys_to_delete:
            ids_to_delete = [
                card.id
                for card in existing_cards
                if (card.file_path, card.full_name) in keys_to_delete
            ]
            if ids_to_delete:
                cards_to_delete = db_session.exec(
                    select(Card).where(col(Card.id).in_(ids_to_delete))
                ).all()
                for card in cards_to_delete:
                    db_session.delete(card)

        db_session.commit()

    finally:
        if db_gen:
            try:
                next(db_gen)
            except StopIteration:
                pass

    print(f"\n✅ Сканирование завершено. Репозиторий: {repo_path}")
