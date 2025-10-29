import os

import httpx
import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.database import Base, get_async_session
from main import app
from tests.fixtures import (  # noqa: F401
    another_user,
    project,
    projects,
    user,
    users,
)


@pytest.fixture(scope='session', autouse=True)
def set_testing_env():
    """Устанавливает переменную окружения TESTING."""
    os.environ['TESTING'] = 'True'
    yield
    os.environ.pop('TESTING', None)


@pytest.fixture(scope='session')
async def db_engine():
    db_url = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql+asyncpg://postgres:postgres@localhost/alchemy_db_test',
    )
    engine = create_async_engine(db_url, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_session(db_engine) -> AsyncSession:
    """Сессия с SAVEPOINT: код под тестом может делать commit()/rollback()."""
    async with db_engine.connect() as conn:
        transaction = await conn.begin()

        async_session = async_sessionmaker(
            bind=conn, expire_on_commit=False, autoflush=False
        )
        session: AsyncSession = async_session()

        await session.begin_nested()

        @event.listens_for(session.sync_session, 'after_transaction_end')
        def restart_savepoint(sess, txn):
            if txn.nested and not txn._parent.nested:
                sess.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def client(test_session):
    """Создание HTTP-клиента с подменой зависимости get_async_session."""

    async def _override_session():
        yield test_session

    app.dependency_overrides[get_async_session] = _override_session

    transport = httpx.ASGITransport(app=app, lifespan='on')
    async with httpx.AsyncClient(
        transport=transport, base_url='http://test'
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
