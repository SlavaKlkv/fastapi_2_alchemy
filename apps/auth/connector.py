from __future__ import annotations

from typing import cast

from apps.user.models import UserRecord, to_public
from apps.user.repository import UserRepository
from apps.user.schemas import User, UserCreate
from apps.user.services import UserService
from core.security import verify_password

_service = UserService()
_repo = UserRepository()


def get_user_by_username(username: str) -> User | None:
    """Найти пользователя по username (используется при логине/регистрации)."""
    return _repo.get_by_username(username)


def create_user(payload: UserCreate) -> User:
    """
    Регистрация пользователя через user-service
    (хеширование выполняется в сервисе).
    """
    return _service.create_user(payload)


def authenticate_credentials(login: str, password: str) -> User | None:
    """
    Аутентифицировать пользователя по username/email и паролю.
    Возврат публичной модели User при успешной проверке.
    """
    login = login.casefold().strip()
    if '@' in login:
        rec = _repo.get_raw_by_email(login)
    else:
        rec = _repo.get_raw_by_username(login)
    if not rec:
        return None
    hashed = rec.get('hashed_password') or ''
    if hashed and verify_password(password, hashed):
        return to_public(cast(UserRecord, rec))
    return None
