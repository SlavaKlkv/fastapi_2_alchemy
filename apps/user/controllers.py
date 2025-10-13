from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.schemas import (
    User,
    UserCreate,
    UserDeleteResponse,
    UsersList,
    UserUpdate,
)
from apps.user.services import UserService
from core.database import get_async_session


class UserController:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session
        self.service = UserService(session)

    async def get_user(self, user_id: int) -> User:
        return await self.service.get_user(user_id)

    async def get_users_by_ids(self, user_ids: list[int]) -> UsersList:
        users = await self.service.get_users_by_ids(user_ids)
        return UsersList(users=users)

    async def get_all_users(self) -> UsersList:
        users = await self.service.get_all_users()
        return UsersList(users=users)

    async def create_user(self, payload: UserCreate) -> User:
        return await self.service.create_user(payload)

    async def create_users(self, payloads: list[UserCreate]) -> UsersList:
        users = await self.service.create_users(payloads)
        return UsersList(users=users)

    async def update_user(self, user_id: int, payload: UserUpdate) -> User:
        return await self.service.update_user(user_id, payload)

    async def delete_user(self, user_id: int) -> UserDeleteResponse:
        return await self.service.delete_user(user_id)
