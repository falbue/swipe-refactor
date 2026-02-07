from logging.config import fileConfig
from alembic import context
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(APP_DIR))

try:
    from dotenv import load_dotenv

    load_dotenv(APP_DIR / ".env")
except ImportError:
    raise RuntimeError("python-dotenv is required for Alembic to load .env")


from sqlmodel import SQLModel  # noqa: E402
from sqlmodel.sql.sqltypes import AutoString, GUID  # noqa: E402

# Импортируем модели — они могут зависеть от engine или других частей app
from app.models import *  # noqa: E402, F403

# Импортируем engine ТОЛЬКО после загрузки .env
from app.db.session import engine  # noqa: E402


def render_item(type_, obj, autogen_context):
    if type_ == "type":
        if isinstance(obj, GUID):
            autogen_context.imports.add(
                "from sqlalchemy.dialects.postgresql import UUID"
            )
            return "UUID(as_uuid=True)"

        if isinstance(obj, AutoString):
            autogen_context.imports.add("from sqlalchemy import String")
            if obj.length is not None:
                return f"String({obj.length})"
            else:
                return "String()"

    return False


# Alembic config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = os.getenv("DB_HOST")  # Берём из .env, а не из alembic.ini
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_item=render_item,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
