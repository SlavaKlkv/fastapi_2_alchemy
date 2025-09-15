import os
from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Setting(BaseSettings):
    PRODUCTION: bool = False

    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'postgres'
    DB_PASS: str = 'postgres'
    DB_NAME: str = 'postgres'

    SECRET_KEY: str = 'SECRET_KEY'
    ALGORITHM: str = 'HS256'
    ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 7

    model_config = SettingsConfigDict(
        extra='allow',
        env_file=os.path.abspath(os.path.join(BASE_DIR, '.env')),
    )

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
