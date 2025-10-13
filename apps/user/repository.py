from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.models import User
from apps.user.schemas import (
    User as UserSchema,
)
from apps.user.schemas import (
    UserCreate,
    UserDeleteResponse,
    UserUpdate,
)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------- helpers -------------------------

    @staticmethod
    def _to_schema(obj: User) -> UserSchema:
        return UserSchema.model_validate(obj)

    # ------------------------- queries -------------------------

    async def get_raw_by_email(self, email: str) -> User | None:
        """
        SQL:
        SELECT u.*
        FROM users AS u
        WHERE lower(trim(u.email)) = lower(trim(:email))
        LIMIT 1;
        """
        stmt = (
            select(User)
            .where(
                func.lower(func.trim(User.email))
                == func.lower(func.trim(email))
            )
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_raw_by_username(self, username: str) -> User | None:
        """
        SQL:
        SELECT u.*
        FROM users AS u
        WHERE lower(trim(u.username)) = lower(trim(:username))
        LIMIT 1;
        """
        stmt = (
            select(User)
            .where(
                func.lower(func.trim(User.username))
                == func.lower(func.trim(username))
            )
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_username(self, username: str) -> UserSchema | None:
        """
        SQL:
        SELECT u.*
        FROM users AS u
        WHERE lower(trim(u.username)) = lower(trim(:username))
        LIMIT 1;
        """
        obj = await self.get_raw_by_username(username)
        return self._to_schema(obj) if obj else None

    async def get_by_id(self, user_id: int) -> UserSchema | None:
        """
        SQL:
        SELECT u.*
        FROM users AS u
        WHERE u.id = :user_id
        LIMIT 1;
        """
        res = await self.session.execute(
            select(User).where(User.id == user_id).limit(1)
        )
        obj = res.scalar_one_or_none()
        return self._to_schema(obj) if obj else None

    async def get_several_by_ids(self, ids: Iterable[int]) -> list[UserSchema]:
        """
        SQL:
        SELECT u.*
        FROM users AS u
        WHERE u.id = ANY(:ids);
        """
        id_list = list(ids)
        if not id_list:
            return []
        res = await self.session.execute(
            select(User).where(User.id.in_(id_list))
        )
        objs: Sequence[User] = res.scalars().all()
        return [self._to_schema(o) for o in objs]

    async def get_all(self) -> list[UserSchema]:
        """
        SQL:
        SELECT u.*
        FROM users AS u
        ORDER BY u.id ASC;
        """
        res = await self.session.execute(select(User).order_by(User.id.asc()))
        objs: Sequence[User] = res.scalars().all()
        return [self._to_schema(o) for o in objs]

    # ------------------------- mutations -------------------------

    async def create(self, payload: UserCreate, pwd_hash: str) -> UserSchema:
        """
        SQL:
        INSERT INTO users
            (username, email, full_name, hashed_password)
        VALUES (:username, :email, :full_name, :disabled, :hashed_password)
        RETURNING *;
        """
        obj = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=pwd_hash,
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return self._to_schema(obj)

    async def create_several(
        self, payloads: list[tuple[UserCreate, str]]
    ) -> list[UserSchema]:
        """
        SQL:
        INSERT INTO users
            (username, email, full_name, hashed_password)
        VALUES (:username, :email, :full_name, :disabled, :hashed_password)
        RETURNING *; -- повторяется для каждой записи
        """
        created: list[UserSchema] = []
        for payload, pwd_hash in payloads:
            obj = User(
                username=payload.username,
                email=payload.email,
                full_name=payload.full_name,
                hashed_password=pwd_hash,
            )
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            created.append(self._to_schema(obj))
        return created

    async def update(
        self, user_id: int, payload: UserUpdate
    ) -> UserSchema | None:
        """
        SQL:
        UPDATE users
        SET
            username = COALESCE(:username, username),
            email = COALESCE(:email, email),
            full_name = COALESCE(:full_name, full_name),
            hashed_password = COALESCE(:hashed_password, hashed_password),
        WHERE id = :user_id
        RETURNING *;
        """
        obj_res = await self.session.execute(
            select(User).where(User.id == user_id).limit(1)
        )
        obj = obj_res.scalar_one_or_none()
        if obj is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        if 'password' in data:
            data['hashed_password'] = data.pop('password')

        for key, value in data.items():
            setattr(obj, key, value)

        await self.session.flush()
        await self.session.refresh(obj)
        return self._to_schema(obj)

    async def delete(self, user_id: int) -> UserDeleteResponse | None:
        """
        SQL:
        DELETE FROM users
        WHERE id = :user_id
        RETURNING *;
        """
        res = await self.session.execute(
            select(User).where(User.id == user_id).limit(1)
        )
        obj = res.scalar_one_or_none()
        if obj is None:
            return None

        await self.session.delete(obj)
        return UserDeleteResponse(
            id=obj.id,
            username=obj.username,
            email=obj.email,
            full_name=obj.full_name,
            disabled=obj.disabled,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )
