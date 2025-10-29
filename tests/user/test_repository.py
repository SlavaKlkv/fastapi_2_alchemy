import hmac

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.models import User
from apps.user.repository import UserRepository
from apps.user.schemas import UserCreate, UserUpdate


@pytest.fixture
def repo(test_session: AsyncSession) -> UserRepository:
    return UserRepository(test_session)


@pytest.mark.database
class TestUserRepository:
    async def test_get_raw_by_email_case_insensitive_and_trim(
        self, repo: UserRepository, user
    ):
        found = await repo.get_raw_by_email(f'  {user.email.upper()}  ')
        assert found is not None
        assert found.id == user.id

    async def test_get_raw_by_username_case_insensitive_and_trim(
        self, repo: UserRepository, user
    ):
        found = await repo.get_raw_by_username(f'  {user.username.upper()}  ')
        assert found is not None
        assert found.id == user.id

    async def test_get_by_id(self, repo: UserRepository, user):
        fetched = await repo.get_by_id(user.id)
        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.username == user.username
        assert fetched.email == user.email

    async def test_get_by_username(self, repo: UserRepository, users):
        target = users[1]
        fetched = await repo.get_by_username(target.username.upper())
        assert fetched is not None
        assert fetched.id == target.id
        assert fetched.username == target.username
        assert fetched.email == target.email

    async def test_get_several_by_ids(self, repo: UserRepository, users):
        ids = [users[0].id, users[2].id]
        result = await repo.get_several_by_ids(ids)

        assert isinstance(result, list)
        assert len(result) == 2
        returned_ids = [u.id for u in result]
        assert set(returned_ids) == set(ids)
        assert all(u.id in ids for u in result)

    async def test_get_several_by_ids_empty_list(self, repo: UserRepository):
        result = await repo.get_several_by_ids([])
        assert result == []

    async def test_get_all(self, repo: UserRepository, users):
        result = await repo.get_all()

        assert isinstance(result, list)
        assert len(result) == len(users)
        ids = [u.id for u in result]
        assert ids == sorted(ids)
        expected_ids = sorted(u.id for u in users)
        assert ids == expected_ids

    async def test_create_user(self, repo: UserRepository, test_session):
        payload = UserCreate(
            username='new_user',
            email='new_user@example.com',
            full_name='Новый пользователь',
            password='plain_test_passw0rd',
        )
        pwd_hash = 'hashed_password_123'

        created = await repo.create(payload, pwd_hash=pwd_hash)

        assert created.username == payload.username
        assert created.email == payload.email
        assert created.full_name == payload.full_name

        res = await test_session.execute(
            select(User).where(User.username == payload.username)
        )
        user_in_db = res.scalar_one_or_none()

        assert user_in_db is not None
        assert user_in_db.hashed_password == pwd_hash
        assert user_in_db.username == payload.username
        assert user_in_db.email == payload.email

    async def test_create_several_users(
        self, repo: UserRepository, test_session
    ):
        payloads = [
            (
                UserCreate(
                    username=f'user_{i}',
                    email=f'user_{i}@example.com',
                    full_name=f'Пользователь {i}',
                    password='plain_passw0rd',
                ),
                f'hash_{i}',
            )
            for i in range(3)
        ]

        created_users = await repo.create_several(payloads)

        assert len(created_users) == 3

        for i, user_schema in enumerate(created_users):
            assert user_schema.username == f'user_{i}'
            assert user_schema.email == f'user_{i}@example.com'
            assert user_schema.full_name == f'Пользователь {i}'

        res = await test_session.execute(select(User))
        users_in_db = res.scalars().all()
        db_usernames = [u.username for u in users_in_db]
        for i in range(3):
            assert f'user_{i}' in db_usernames

    async def test_update_user(self, repo: UserRepository, test_session, user):
        update_data = UserUpdate(
            email='updated_email@example.com',
            full_name='Обновленное имя',
            password='new_passw0rd',
        )
        updated = await repo.update(user.id, update_data)

        assert updated is not None
        assert updated.id == user.id
        assert updated.email == update_data.email
        assert updated.full_name == update_data.full_name

        res = await test_session.execute(
            select(User).where(User.id == user.id)
        )
        user_in_db = res.scalar_one_or_none()
        assert user_in_db is not None
        assert user_in_db.email == update_data.email
        assert user_in_db.full_name == update_data.full_name
        assert hmac.compare_digest(
            user_in_db.hashed_password, update_data.password
        )

    async def test_delete_user(self, repo: UserRepository, test_session, user):
        deleted = await repo.delete(user.id)
        await test_session.flush()

        assert deleted is not None
        assert deleted.id == user.id
        assert deleted.username == user.username
        assert deleted.email == user.email
        assert deleted.full_name == user.full_name
        assert deleted.disabled == user.disabled

        res = await test_session.execute(
            select(User).where(User.id == user.id)
        )
        user_in_db = res.scalar_one_or_none()
        assert user_in_db is None

    async def test_delete_nonexistent_user(self, repo: UserRepository):
        deleted = await repo.delete(9999)
        assert deleted is None
