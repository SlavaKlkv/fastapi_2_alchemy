from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    TESTING: bool = False

    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'postgres'
    DB_PASSWORD: str = 'postgres'
    DB_NAME: str = 'alchemy_db'
    DB_NAME_TEST: str = 'alchemy_db_test'
    DB_ECHO: bool = False

    SECRET_KEY: str = 'SECRET_KEY'
    ALGORITHM: str = 'HS256'
    ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 7

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @property
    def _db_name(self) -> str:
        return self.DB_NAME_TEST if self.TESTING else self.DB_NAME

    @property
    def db_connection_url(self) -> str:
        """Асинхронный URL (используется приложением)."""
        user = quote(self.DB_USER)
        password = quote(self.DB_PASSWORD)
        hostport = (
            f'{self.DB_HOST}:{self.DB_PORT}' if self.DB_PORT else self.DB_HOST
        )
        return (
            f'postgresql+asyncpg://{user}:{password}'
            f'@{hostport}/{self._db_name}'
        )

    @property
    def db_connection_url_sync(self) -> str:
        """Синхронный URL (Alembic offline/инструменты)."""
        user = quote(self.DB_USER)
        password = quote(self.DB_PASSWORD)
        hostport = (
            f'{self.DB_HOST}:{self.DB_PORT}' if self.DB_PORT else self.DB_HOST
        )
        return f'postgresql://{user}:{password}@{hostport}/{self._db_name}'


settings = Settings()
