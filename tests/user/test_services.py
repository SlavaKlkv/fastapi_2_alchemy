import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.models import User
from apps.user.schemas import UserCreate, UserUpdate
from apps.user.services import UserService
from core.exceptions import UserAlreadyExistsException, UserNotFoundException


@pytest.fixture
def service(test_session: AsyncSession) -> UserService:
    return UserService(test_session)


@pytest.mark.services
class TestUserService:
    async def test_get_user_ok(self, service: UserService, user):
        got = await service.get_user(user.id)
        assert got.id == user.id
        assert got.username == user.username
        assert got.email == user.email

    async def test_get_user_not_found(self, service: UserService):
        with pytest.raises(UserNotFoundException):
            await service.get_user(999_999)

    async def test_get_users_by_ids(self, service: UserService, users):
        ids = [users[0].id, users[2].id]
        got = await service.get_users_by_ids(ids)
        assert sorted(u.id for u in got) == sorted(ids)

    async def test_get_all_users(self, service: UserService, users):
        got = await service.get_all_users()
        assert [u.id for u in got] == sorted(u.id for u in users)

    async def test_create_user_ok(
        self, service: UserService, test_session, monkeypatch
    ):
        monkeypatch.setattr(
            'apps.user.services.hash_password',
            lambda p: 'HASHED!',
            raising=True,
        )

        payload = UserCreate(
            username='svc_new_user',
            email='svc_new_user@example.com',
            full_name='Новый пользователь',
            password='plainpassw0rd',
        )

        created = await service.create_user(payload)
        assert created.username == 'svc_new_user'
        assert created.email == 'svc_new_user@example.com'

        res = await test_session.execute(
            select(User).where(User.username == 'svc_new_user')
        )
        user_in_db = res.scalar_one()
        assert user_in_db.hashed_password == 'HASHED!'

    async def test_create_user_conflict_username(
        self, service: UserService, user
    ):
        payload = UserCreate(
            username=user.username,
            email='another@example.com',
            full_name='Дубликат',
            password='x1',
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.create_user(payload)

    async def test_create_user_conflict_email(
        self, service: UserService, user
    ):
        payload = UserCreate(
            username='unique_login',
            email=user.email,
            full_name='Дубликат',
            password='x1',
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.create_user(payload)

    async def test_create_users_ok(
        self, service: UserService, test_session, monkeypatch
    ):
        monkeypatch.setattr(
            'apps.user.services.hash_password',
            lambda p: f'H:{p}',
            raising=True,
        )

        payloads = [
            UserCreate(
                username=f'bulk{i}',
                email=f'bulk{i}@ex.com',
                full_name=f'Пользователь {i}',
                password=f'p{i}',
            )
            for i in range(3)
        ]

        created = await service.create_users(payloads)
        assert len(created) == 3

        res = await test_session.execute(
            select(User).where(
                User.username.in_([f'bulk{i}' for i in range(3)])
            )
        )
        assert len(res.scalars().all()) == 3

    async def test_create_users_duplicate_raises(
        self, service: UserService, users
    ):
        dup = UserCreate(
            username=users[0].username,
            email='dup@example.com',
            full_name='Дубликат',
            password='p1',
        )
        with pytest.raises(UserAlreadyExistsException):
            await service.create_users([dup])

    async def test_update_user_ok(
        self, service: UserService, test_session, user, monkeypatch
    ):
        monkeypatch.setattr(
            'apps.user.services.hash_password',
            lambda p: 'HPASS',
            raising=True,
        )

        upd = UserUpdate(
            email='upd@example.com',
            full_name='Обновлён',
            password='secretpassw0rd',
        )

        updated = await service.update_user(user.id, upd)
        assert updated.email == 'upd@example.com'

        res = await test_session.execute(
            select(User).where(User.id == user.id)
        )
        user_in_db = res.scalar_one()
        assert user_in_db.hashed_password == 'HPASS'

    async def test_update_user_not_found(self, service: UserService):
        with pytest.raises(UserNotFoundException):
            await service.update_user(999_999, UserUpdate(full_name='X'))

    async def test_delete_user_ok(
        self, service: UserService, test_session, user
    ):
        resp = await service.delete_user(user.id)
        assert resp.id == user.id

        await test_session.flush()
        res = await test_session.execute(
            select(User).where(User.id == user.id)
        )
        assert res.scalar_one_or_none() is None
