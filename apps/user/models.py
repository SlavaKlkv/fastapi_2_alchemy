import re
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from core.constants import (
    FULL_NAME_MIN_LENGTH,
    PASSWORD_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)


class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,  # повторная валидация при изменении полей
    )

    USERNAME_RE: ClassVar[re.Pattern[str]] = re.compile(r'^[a-z0-9_.-]+$')

    id: int = Field(
        ..., gt=0, description='Положительный идентификатор пользователя'
    )
    username: str = Field(
        ...,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        description='Уникальный логин (3–30)',
    )
    email: EmailStr = Field(..., description='Корректный e-mail')
    full_name: str | None = Field(
        default=None,
        min_length=FULL_NAME_MIN_LENGTH,
        max_length=FULL_NAME_MIN_LENGTH,
        description='Имя и фамилия (опционально)',
    )
    disabled: bool = Field(
        default=False, description='Признак блокировки пользователя'
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not cls.USERNAME_RE.fullmatch(v.casefold().strip()):
            raise ValueError(
                'username может содержать только '
                "латинские буквы, цифры, символы '._-'"
            )
        return v

    @field_validator('full_name')
    def validate_full_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.strip() == '':
            raise ValueError('full_name не может быть пустой строкой')
        return v


class UserInDB(User):
    hashed_password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        description='Хэш пароля (не пустой)',
    )
