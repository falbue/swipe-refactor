from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорировать лишние переменные
    )

    DB_USERNAME: str = Field(
        default="admin",
        description="Имя пользователя базы данных",
    )
    DB_PASSWORD: str = Field(
        default="strong_password",
        description="Пароль базы данных",
    )
    DB_HOST: str = Field(
        default="localhost",
        description="Хост базы данных",
    )
    DB_PORT: int = Field(
        default=5432,
        description="Порт базы данных",
    )
    DB_NAME: str = Field(
        default="myapp_db",
        description="Имя базы данных",
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Включить логирование SQL-запросов (true/false)",
    )
    TEMP_REPO_PATH: str = Field(
        default="repositories",
        description="Папка для временных репозиториев при анализе",
    )


# Автоматическое создание .env шаблона при отсутствии файла
env_path = Path(".env")
if not env_path.exists():
    with open(env_path, "w", encoding="utf-8") as f:
        for field_name, field_info in DatabaseSettings.model_fields.items():
            desc = field_info.description or ""
            default = field_info.get_default()
            if isinstance(default, bool):
                default = "true" if default else "false"
            else:
                default = str(default)

            f.write(f"# {desc}\n")
            f.write(f"{field_name}={default}\n\n")

    raise RuntimeError(
        "Файл .env не найден и был создан со шаблоном.\n"
        "Отредактируйте параметры перед запуском:\n"
        f"- Файл: {env_path.absolute()}"
    )

# Создание экземпляра конфигурации
config = DatabaseSettings()
