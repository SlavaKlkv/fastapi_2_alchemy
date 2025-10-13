from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.controllers import UserController
from apps.user.schemas import (
    User,
    UserCreate,
    UserDeleteResponse,
    UsersList,
    UserUpdate,
)
from core.database import get_async_session
from core.security import current_subject

users_router = APIRouter(
    prefix='/users',
    tags=['users'],
    dependencies=[Depends(current_subject)],
)


async def get_controller(
    session: AsyncSession = Depends(get_async_session),
) -> UserController:
    return UserController(session)


@users_router.get(
    '/{user_id}', response_model=User, summary='Получить пользователя по ID'
)
async def get_user(
    user_id: int,
    controller: UserController = Depends(get_controller),
) -> User:
    return await controller.get_user(user_id)


@users_router.get(
    '/',
    response_model=UsersList,
    summary='Получить пользователей: по списку id или всех',
)
async def get_users(
    ids: list[int] | None = Query(
        default=None, description='Список ID для фильтрации'
    ),
    controller: UserController = Depends(get_controller),
) -> UsersList:
    if ids:
        return await controller.get_users_by_ids(ids)
    return await controller.get_all_users()


@users_router.post(
    '/',
    response_model=User,
    status_code=201,
    summary='Создать одного пользователя',
)
async def create_user(
    payload: UserCreate,
    controller: UserController = Depends(get_controller),
) -> User:
    return await controller.create_user(payload)


@users_router.post(
    '/bulk',
    response_model=UsersList,
    status_code=201,
    summary='Создать несколько пользователей',
)
async def create_users(
    payloads: list[UserCreate],
    controller: UserController = Depends(get_controller),
) -> UsersList:
    return await controller.create_users(payloads)


@users_router.patch(
    '/{user_id}', response_model=User, summary='Обновить пользователя'
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    controller: UserController = Depends(get_controller),
) -> User:
    return await controller.update_user(user_id, payload)


@users_router.delete(
    '/{user_id}',
    response_model=UserDeleteResponse,
    summary='Удалить пользователя и вернуть его данные',
)
async def delete_user(
    user_id: int,
    controller: UserController = Depends(get_controller),
) -> UserDeleteResponse:
    return await controller.delete_user(user_id)
