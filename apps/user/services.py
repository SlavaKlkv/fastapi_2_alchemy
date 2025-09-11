from typing import Iterable, List

from apps.user.repository import UserRepository
from apps.user.schemas import User, UserCreate, UserUpdate
from core.exceptions import UserAlreadyExistsException, UserNotFoundException


class UserService:
    def __init__(self, repository: UserRepository | None = None) -> None:
        self._repository = repository or UserRepository()

    # ------------------------- queries -------------------------

    def get_user(self, user_id: int) -> User | None:
        user = self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        return user

    def get_users_by_ids(self, ids: Iterable[int]) -> list[User]:
        return self._repository.get_several_by_ids(ids)

    def get_all_users(self) -> list[User]:
        return self._repository.get_all()

    # ------------------------- mutations -------------------------

    def create_user(self, payload: UserCreate) -> User:
        if any(
            u.username == payload.username for u in self._repository.get_all()
        ):
            raise UserAlreadyExistsException('username')
        return self._repository.create(payload)

    def create_users(self, payloads: List[UserCreate]) -> list[User]:
        existing_usernames = {u.username for u in self._repository.get_all()}
        for payload in payloads:
            if payload.username in existing_usernames:
                raise UserAlreadyExistsException('username')
        return self._repository.create_several(payloads)

    def update_user(self, user_id: int, payload: UserUpdate) -> User | None:
        user = self._repository.update(user_id, payload)
        if user is None:
            raise UserNotFoundException(user_id)
        return user

    def delete_user(self, user_id: int) -> User | None:
        user = self._repository.delete(user_id)
        if user is None:
            raise UserNotFoundException(user_id)
        return user
