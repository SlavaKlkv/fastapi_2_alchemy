from apps.user.schemas import (
    User,
    UserCreate,
    UserDeleteResponse,
    UsersList,
    UserUpdate,
)
from apps.user.services import UserService


class UserController:
    def __init__(self, service: UserService | None = None):
        self.service = service or UserService()

    def get_user(self, user_id: int) -> User:
        return self.service.get_user(user_id)

    def get_users_by_ids(self, user_ids: list[int]) -> UsersList:
        users = self.service.get_users_by_ids(user_ids)
        return UsersList(users=users)

    def get_all_users(self) -> UsersList:
        users = self.service.get_all_users()
        return UsersList(users=users)

    def create_user(self, payload: UserCreate) -> User:
        return self.service.create_user(payload)

    def create_users(self, payloads: list[UserCreate]) -> UsersList:
        users = self.service.create_users(payloads)
        return UsersList(users=users)

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        return self.service.update_user(user_id, payload)

    def delete_user(self, user_id: int) -> UserDeleteResponse:
        return self.service.delete_user(user_id)
