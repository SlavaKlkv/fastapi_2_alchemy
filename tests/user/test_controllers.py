import types

import pytest

from apps.user.controllers import UserController
from apps.user.schemas import (
    User as UserSchema,
)
from apps.user.schemas import (
    UserCreate,
    UserDeleteResponse,
    UsersList,
    UserUpdate,
)
from core.exceptions import UserAlreadyExistsException, UserNotFoundException

# ---------------------------- helpers -----------------------------


def _mk_user(id_: int = 1, username: str = 'user1') -> UserSchema:
    return UserSchema(
        id=id_,
        username=username,
        email=f'{username}@example.com',
        full_name='Test User',
        disabled=False,
    )


# ---------------------------- fixtures -----------------------------


@pytest.fixture
def fake_service():
    """
    Простейший «сервис» как объект с атрибутами-корутинами.
    В каждом тесте подменяются нужные методы.
    """
    return types.SimpleNamespace()


@pytest.fixture
def controller(fake_service, monkeypatch) -> UserController:
    controller = UserController()
    controller.service = fake_service
    return controller


# ---------------------------- tests -----------------------------


@pytest.mark.controllers
class TestUserController:
    async def test_get_user_ok(self, controller: UserController, fake_service):
        user = _mk_user(10, 'john')

        async def _get_user(user_id: int):
            assert user_id == 10
            return user

        fake_service.get_user = _get_user

        result = await controller.get_user(10)
        assert isinstance(result, UserSchema)
        assert result.id == 10
        assert result.username == 'john'

    async def test_get_user_not_found_raises(
        self, controller: UserController, fake_service
    ):
        async def _get_user(_):
            raise UserNotFoundException('nope')

        fake_service.get_user = _get_user

        with pytest.raises(UserNotFoundException):
            await controller.get_user(999)

    async def test_get_users_by_ids(
        self, controller: UserController, fake_service
    ):
        ids = [1, 3, 5]
        users = [_mk_user(i, f'user{i}') for i in ids]

        async def _get_users_by_ids(user_ids: list[int]):
            assert user_ids == ids
            return users

        fake_service.get_users_by_ids = _get_users_by_ids

        result = await controller.get_users_by_ids(ids)
        assert isinstance(result, UsersList)
        assert [u.id for u in result.users] == ids

    async def test_get_all_users(
        self, controller: UserController, fake_service
    ):
        users = [_mk_user(1, 'user1'), _mk_user(2, 'user2')]

        async def _get_all_users():
            return users

        fake_service.get_all_users = _get_all_users

        result = await controller.get_all_users()
        assert isinstance(result, UsersList)
        assert [u.username for u in result.users] == ['user1', 'user2']

    async def test_create_user(self, controller: UserController, fake_service):
        payload = UserCreate(
            username='new_user',
            email='new_user@example.com',
            full_name='Новый пользователь',
            password='p1',
        )
        created = _mk_user(42, 'new_user')

        async def _create_user(p: UserCreate):
            assert p == payload
            return created

        fake_service.create_user = _create_user

        result = await controller.create_user(payload)
        assert isinstance(result, UserSchema)
        assert result.id == 42
        assert result.username == 'new_user'

    async def test_create_user_conflict_raises(
        self, controller: UserController, fake_service
    ):
        async def _create_user(_):
            raise UserAlreadyExistsException('dup')

        fake_service.create_user = _create_user

        with pytest.raises(UserAlreadyExistsException):
            await controller.create_user(
                UserCreate(
                    username='dup',
                    email='dup@example.com',
                    full_name='Дубликат',
                    password='x1',
                )
            )

    async def test_create_users(
        self, controller: UserController, fake_service
    ):
        payloads = [
            UserCreate(
                username=f'user{i}',
                email=f'u{i}@ex.com',
                full_name=f'U{i}',
                password=f'p{i}',
            )
            for i in range(3)
        ]
        created = [_mk_user(i + 1, f'user{i}') for i in range(3)]

        async def _create_users(ps: list[UserCreate]):
            assert ps == payloads
            return created

        fake_service.create_users = _create_users

        result = await controller.create_users(payloads)
        assert isinstance(result, UsersList)
        assert [u.username for u in result.users] == [
            'user0',
            'user1',
            'user2',
        ]

    async def test_update_user(self, controller: UserController, fake_service):
        updated_user = _mk_user(7, 'upd_user')
        upd = UserUpdate(
            email='upd@example.com', full_name='Обновлён', password='password1'
        )

        async def _update_user(user_id: int, payload: UserUpdate):
            assert user_id == 7
            assert payload == upd
            return updated_user

        fake_service.update_user = _update_user

        result = await controller.update_user(7, upd)
        assert isinstance(result, UserSchema)
        assert result.id == 7
        assert result.username == 'upd_user'

    async def test_delete_user(self, controller: UserController, fake_service):
        resp = UserDeleteResponse(
            id=5,
            username='victim',
            email='victim@example.com',
            full_name='To Delete',
            disabled=False,
            deleted=True,
        )

        async def _delete_user(user_id: int):
            assert user_id == 5
            return resp

        fake_service.delete_user = _delete_user

        result = await controller.delete_user(5)
        assert isinstance(result, UserDeleteResponse)
        assert result.id == 5
        assert result.deleted is True
