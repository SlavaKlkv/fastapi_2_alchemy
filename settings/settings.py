from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Setting(BaseSettings):
    PRODUCTION: bool | None = False

    DB_HOST: str | None = 'localhost'
    DB_PORT: int | None = 5432
    DB_USER: str | None = 'postgres'
    DB_PASS: str | None = 'postgres'
    DB_NAME: str | None = 'fa_alchemy'
    DB_ECHO: bool | None = False

    SECRET_KEY: str | None = 'SECRET_KEY'
    ALGORITHM: str | None = 'HS256'
    ACCESS_TTL_MIN: int | None = 15
    REFRESH_TTL_DAYS: int | None = 7

    model_config = SettingsConfigDict(extra='allow')

    @property
    def db_connection_url(self) -> str:
        """
        Возврат строки с адресом подключения к базе данных.
        """
        user = quote(self.DB_USER)
        password = quote(self.DB_PASS)
        hostport = (
            f'{self.DB_HOST}:{self.DB_PORT}' if self.DB_PORT else self.DB_HOST
        )
        return (
            f'postgresql+asyncpg://{user}:{password}@{hostport}/{self.DB_NAME}'
        )

    @property
    def db_connection_url_sync(self) -> str:
        """
        Возврат строки подключения к базе данных
        для синхронного режима (Alembic offline).
        """
        user = quote(self.DB_USER)
        password = quote(self.DB_PASS)
        hostport = (
            f'{self.DB_HOST}:{self.DB_PORT}' if self.DB_PORT else self.DB_HOST
        )
        return f'postgresql://{user}:{password}@{hostport}/{self.DB_NAME}'


settings = Setting()
