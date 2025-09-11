from __future__ import annotations

from typing import Iterable

from apps.user.schemas import User, UserCreate, UserUpdate
from core.store import DatabaseSession


class UserRepository:
    USERS_KEY = 'users'

    # ------------------------- helpers -------------------------

    def _ensure_bucket(self, root: dict) -> dict[int, dict]:
        """
        Гарантирует наличие раздела 'users' в корне хранилища и возвращает его.
        """
        bucket = root.get(self.USERS_KEY)
        if bucket is None:
            bucket = {}
            root[self.USERS_KEY] = bucket
        return bucket

    def _next_id(self, bucket: dict[int, dict]) -> int:
        return max(bucket.keys(), default=0) + 1

    def _dump_user(self, payload: UserCreate, new_id: int) -> dict:
        """Преобразует входные данные пользователя в словарь для хранения."""
        data = payload.model_dump()
        if 'password' in data and 'hashed_password' not in data:
            data['hashed_password'] = data.pop('password')
        data.setdefault('disabled', False)
        data['id'] = new_id
        return data

    def _apply_updates(self, target: dict, patch: UserUpdate) -> None:
        updates = patch.model_dump(exclude_unset=True)
        if 'password' in updates:
            target['hashed_password'] = updates.pop('password')
        target.update(updates)

    # ------------------------- queries -------------------------

    def get_by_id(self, user_id: int) -> User | None:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            raw = users.get(user_id)
        return User(**raw) if raw else None

    def get_several_by_ids(self, ids: Iterable[int]) -> list[User]:
        id_set = set(ids)
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            raw_data = [u for uid, u in users.items() if uid in id_set]
        return [User(**r) for r in raw_data]

    def get_all(self) -> list[User]:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            raw_data = list(users.values())
        return [User(**r) for r in raw_data]

    # ------------------------- mutations -------------------------

    def create(self, payload: UserCreate) -> User:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            new_id = self._next_id(users)
            record = self._dump_user(payload, new_id)
            users[new_id] = record
            store.set_store_data(root)
        return User(**record)

    def create_several(self, payloads: list[UserCreate]) -> list[User]:
        created: list[User] = []
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            for payload in payloads:
                new_id = self._next_id(users)
                record = self._dump_user(payload, new_id)
                users[new_id] = record
                created.append(User(**record))
            store.set_store_data(root)
        return created

    def update(self, user_id: int, payload: UserUpdate) -> User | None:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            if (existing := users.get(user_id)) is None:
                return None
            self._apply_updates(existing, payload)
            users[user_id] = existing
            store.set_store_data(root)
        return User(**existing)

    def delete(self, user_id: int) -> User | None:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            removed = users.pop(user_id, None)
            if removed is not None:
                store.set_store_data(root)
        return User(**removed) if removed else None
