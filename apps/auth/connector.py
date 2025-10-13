from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from apps.user.repository import UserRepository
from apps.user.schemas import User as UserSchema
from apps.user.schemas import UserCreate
from apps.user.services import UserService
from core.security import verify_password


async def get_user_by_username(
    username: str, session: AsyncSession
) -> UserSchema | None:
    """
    Найти пользователя по username (используется при логине/регистрации).
    Делегирует запрос репозиторию.
    """
    repo = UserRepository(session)
    return await repo.get_by_username(username)


async def create_user(
    payload: UserCreate, session: AsyncSession
) -> UserSchema:
    """
    Регистрация пользователя через сервис.
    Хеширование пароля выполняется в сервисе.
    """
    service = UserService(session)
    return await service.create_user(payload)


async def authenticate_credentials(
    login: str, password: str, session: AsyncSession
) -> UserSchema | None:
    """
    Аутентифицировать пользователя по username/email и паролю.
    Возвращает публичную модель User при успешной проверке.
    """
    login_norm = login.casefold().strip()
    repo = UserRepository(session)

    if '@' in login_norm:
        user_obj = await repo.get_raw_by_email(login_norm)
    else:
        user_obj = await repo.get_raw_by_username(login_norm)

    if user_obj is None:
        return None

    hashed = getattr(user_obj, 'hashed_password', '') or ''
    if hashed and verify_password(password, hashed):
        return UserSchema.model_validate(user_obj)

    return None
