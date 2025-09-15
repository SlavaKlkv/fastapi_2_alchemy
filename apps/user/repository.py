from __future__ import annotations

from typing import Iterable

from apps.user.models import UserRecord, to_public, to_record
from apps.user.schemas import User, UserCreate, UserDeleteResponse, UserUpdate
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

    def _apply_updates(self, target: dict, patch: UserUpdate) -> None:
        updates = patch.model_dump(exclude_unset=True)
        if 'password' in updates:
            target['hashed_password'] = updates.pop('password')
        target.update(updates)

    # ------------------------- queries -------------------------

    def get_raw_by_email(self, email: str) -> dict | None:
        normalized = email.casefold().strip()
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            for rec in users.values():
                if (
                    val := rec.get('email')
                ) and val.casefold().strip() == normalized:
                    return rec
        return None

    def get_raw_by_username(self, username: str) -> dict | None:
        normalized = username.casefold().strip()
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            for rec in users.values():
                if (
                    username_val := rec.get('username')
                ) and username_val.casefold().strip() == normalized:
                    return rec
        return None

    def get_by_username(self, username: str) -> User | None:
        rec = self.get_raw_by_username(username)
        return to_public(rec) if rec else None

    def get_by_id(self, user_id: int) -> User | None:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            raw = users.get(user_id)
        return to_public(raw) if raw else None

    def get_several_by_ids(self, ids: Iterable[int]) -> list[User]:
        id_set = set(ids)
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            raw_data = [u for uid, u in users.items() if uid in id_set]
        return [to_public(r) for r in raw_data]

    def get_all(self) -> list[User]:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            raw_data = list(users.values())
        return [to_public(r) for r in raw_data]

    # ------------------------- mutations -------------------------

    def create(self, payload: UserCreate, pwd_hash: str) -> User:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            new_id = self._next_id(users)
            record: UserRecord = to_record(new_id, payload, pwd_hash)
            users[new_id] = record
            store.set_store_data(root)
        return to_public(record)

    def create_several(
        self, payloads: list[tuple[UserCreate, str]]
    ) -> list[User]:
        created: list[User] = []
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            for payload in payloads:
                new_id = self._next_id(users)
                payload_item, pwd_hash = payload
                record: UserRecord = to_record(new_id, payload_item, pwd_hash)
                users[new_id] = record
                created.append(to_public(record))
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
        return to_public(existing)

    def delete(self, user_id: int) -> UserDeleteResponse | None:
        with DatabaseSession() as store:
            root = store.get_store()
            users = self._ensure_bucket(root)
            removed = users.pop(user_id, None)
            if removed is not None:
                store.set_store_data(root)
        return UserDeleteResponse(**removed) if removed else None
