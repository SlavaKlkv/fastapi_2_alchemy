from fastapi import APIRouter, Depends, Query

from apps.user.controllers import UserController
from apps.user.schemas import (
    User,
    UserCreate,
    UserDeleteResponse,
    UsersList,
    UserUpdate,
)
from core.security import current_subject

users_router = APIRouter(
    prefix='/users',
    tags=['users'],
    dependencies=[Depends(current_subject)],
)
_controller = UserController()


@users_router.get(
    '/{user_id}', response_model=User, summary='Получить пользователя по ID'
)
def get_user(user_id: int) -> User:
    return _controller.get_user(user_id)


@users_router.get(
    '/',
    response_model=UsersList,
    summary='Получить пользователей: по списку id или всех',
)
def get_users(
    ids: list[int] | None = Query(
        default=None, description='Список ID для фильтрации'
    ),
) -> UsersList:
    if ids:
        return _controller.get_users_by_ids(ids)
    return _controller.get_all_users()


@users_router.post(
    '/',
    response_model=User,
    status_code=201,
    summary='Создать одного пользователя',
)
def create_user(payload: UserCreate) -> User:
    return _controller.create_user(payload)


@users_router.post(
    '/bulk',
    response_model=UsersList,
    status_code=201,
    summary='Создать несколько пользователей',
)
def create_users(payloads: list[UserCreate]) -> UsersList:
    return _controller.create_users(payloads)


@users_router.patch(
    '/{user_id}', response_model=User, summary='Обновить пользователя'
)
def update_user(user_id: int, payload: UserUpdate) -> User:
    return _controller.update_user(user_id, payload)


@users_router.delete(
    '/{user_id}',
    response_model=UserDeleteResponse,
    summary='Удалить пользователя и вернуть его данные',
)
def delete_user(user_id: int) -> UserDeleteResponse:
    return _controller.delete_user(user_id)
