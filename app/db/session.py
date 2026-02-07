from sqlmodel import create_engine, Session
from sqlalchemy.engine import URL
from core.config import config

# Формируем URL как раньше
db_url = URL.create(
    drivername="postgresql",
    username=config.DB_USERNAME,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=config.DB_PORT,
    database=config.DB_NAME,
)

# Создаём движок
engine = create_engine(db_url, echo=config.DB_ECHO)


def get_db():
    with Session(engine) as session:
        yield session
