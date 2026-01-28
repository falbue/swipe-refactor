import os
import sys
import sqlite3
import time
import fnmatch
from pathlib import Path
from parsers.python_parser import extract_python_entities

# Поддерживаемые расширения
EXTENSIONS = {
    ".py": extract_python_entities,
}

DB_PATH = "cards.db"

# Проверка


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS code_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_path TEXT NOT NULL,
        file_path TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('function', 'class')),
        full_name TEXT NOT NULL,
        simple_name TEXT NOT NULL,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        raw_code TEXT NOT NULL,
        ast_hash BLOB NOT NULL,
        error_message TEXT,
        severity TEXT,
        is_reviewed BOOLEAN DEFAULT 0,
        is_deleted BOOLEAN DEFAULT 0,
        last_seen_at REAL NOT NULL,
        UNIQUE(repo_path, file_path, full_name)
    )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_repo ON code_cards(repo_path);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_last_seen ON code_cards(last_seen_at);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ast_hash ON code_cards(ast_hash);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_kind ON code_cards(kind);")
    conn.commit()
    conn.close()


def scan_repo(repo_path: str):
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

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    scan_time = time.time()

    # Помечаем все карточки из этого репозитория как "не виденные"
    cur.execute(
        "UPDATE code_cards SET last_seen_at = ? WHERE repo_path = ?", (0, repo_path)
    )

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
                cur.execute(
                    """
                    INSERT INTO code_cards (
                        repo_path, file_path, kind, full_name, simple_name,
                        start_line, end_line, raw_code, ast_hash,
                        error_message, severity, last_seen_at, is_deleted
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    ON CONFLICT DO UPDATE SET
                        raw_code = excluded.raw_code,
                        ast_hash = excluded.ast_hash,
                        error_message = excluded.error_message,
                        severity = excluded.severity,
                        last_seen_at = excluded.last_seen_at,
                        is_deleted = 0,
                        is_reviewed = CASE
                            WHEN code_cards.ast_hash != excluded.ast_hash THEN 0
                            ELSE code_cards.is_reviewed
                        END
                """,
                    (
                        repo_path,
                        rel_path,
                        ent["kind"],
                        ent["full_name"],
                        ent["simple_name"],
                        ent["start_line"],
                        ent["end_line"],
                        ent["raw_code"],
                        ent["ast_hash"],
                        ent["error_message"],
                        "medium",
                        scan_time,
                    ),
                )

    # Помечаем удалённые
    cur.execute(
        """
        UPDATE code_cards
        SET is_deleted = 1
        WHERE repo_path = ? AND last_seen_at < ?
    """,
        (repo_path, scan_time),
    )

    conn.commit()
    conn.close()
    print(f"\n✅ Сканирование завершено. Репозиторий: {repo_path}")


if __name__ == "__main__":
    init_db()
    scan_repo(r"D:\coding\work\code\falbue\swipe")
