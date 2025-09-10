import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Setting(BaseSettings):
    PRODUCTION: bool = False

    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'postgres'
    DB_PASS: str = 'postgres'
    DB_NAME: str = 'postgres'
    model_config = SettingsConfigDict(
        extra='allow',
        env_file=os.path.abspath(os.path.join(BASE_DIR, '.env')),
    )
