from __future__ import annotations

from typing import Iterable, List

from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.repository import UserRepository
from apps.user.schemas import (
    User as UserSchema,
)
from apps.user.schemas import (
    UserCreate,
    UserDeleteResponse,
    UserUpdate,
)
from core.exceptions import UserAlreadyExistsException, UserNotFoundException
from core.security import hash_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repository = UserRepository(session)

    # ------------------------- queries -------------------------

    async def get_user(self, user_id: int) -> UserSchema:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        return user

    async def get_users_by_ids(self, ids: Iterable[int]) -> list[UserSchema]:
        return await self._repository.get_several_by_ids(ids)

    async def get_all_users(self) -> list[UserSchema]:
        return await self._repository.get_all()

    # ------------------------- mutations -------------------------

    async def create_user(self, payload: UserCreate) -> UserSchema:
        if await self._repository.get_raw_by_username(payload.username):
            raise UserAlreadyExistsException('username')
        if await self._repository.get_raw_by_email(payload.email):
            raise UserAlreadyExistsException('email')

        pwd_hash = hash_password(payload.password)
        user = await self._repository.create(payload, pwd_hash)
        await self.session.commit()
        return user

    async def create_users(
        self, payloads: List[UserCreate]
    ) -> list[UserSchema]:
        for p in payloads:
            if await self._repository.get_raw_by_username(p.username):
                raise UserAlreadyExistsException('username')
            if await self._repository.get_raw_by_email(p.email):
                raise UserAlreadyExistsException('email')

        payloads_with_hashes = [
            (p, hash_password(p.password)) for p in payloads
        ]
        users = await self._repository.create_several(payloads_with_hashes)
        await self.session.commit()
        return users

    async def update_user(
        self, user_id: int, payload: UserUpdate
    ) -> UserSchema:
        if payload.password is not None:
            payload.password = hash_password(payload.password)

        user = await self._repository.update(user_id, payload)
        if user is None:
            raise UserNotFoundException(user_id)
        await self.session.commit()
        return user

    async def delete_user(self, user_id: int) -> UserDeleteResponse:
        user = await self._repository.delete(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        await self.session.commit()
        return user
