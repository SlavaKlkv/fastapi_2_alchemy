from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from settings.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.db_connection_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False, autocommit=False
)


async def get_async_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
