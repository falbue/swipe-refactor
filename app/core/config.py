import os
from dotenv import load_dotenv
from pathlib import Path
from dotenv import dotenv_values

env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    raise RuntimeError(
        "Файл .env не найден и был создан автоматически.\n"
        "Пожалуйста, настройте его перед запуском:\n"
        f"Файл создан по пути: {env_path.absolute()}"
    )

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_ECHO = os.getenv("DB_ECHO", "False").lower() in ("true", "1", "t")


ENV = {
    "DB_USERNAME": os.getenv("DB_USERNAME"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
    "DB_HOST": os.getenv("DB_HOST"),
    "DB_PORT": int(os.getenv("DB_PORT", 5432)),
    "DB_NAME": os.getenv("DB_NAME"),
    "DB_ECHO": os.getenv("DB_ECHO", "False").lower() in ("true", "1", "t"),
}

for key, value in dotenv_values(env_path).items():
    if not key:
        continue
    if key not in ENV:
        ENV[key] = value

globals().update({key: value for key, value in ENV.items()})
