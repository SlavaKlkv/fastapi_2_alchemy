from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
    validate_email,
)

from apps.user.schemas import User as UserSchema
from core.constants import (
    FULL_NAME_MAX_LENGTH,
    FULL_NAME_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_RE,
)
from utils.validators import (
    validate_full_name_value,
    validate_password_value,
    validate_username_value,
)


class LoginRequest(BaseModel):
    login: str = Field(
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        description='username или email',
    )
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        examples=['string1'],
    )

    @field_validator('login')
    @classmethod
    def validate_login(cls, v: str) -> str:
        normalized = v.casefold().strip()
        if '@' in normalized:
            validate_email(normalized)
            return normalized
        if not USERNAME_RE.fullmatch(normalized):
            raise ValueError(
                'login должен быть username (латиница/цифры/._-) '
                'или корректный e-mail'
            )
        return normalized

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_value(v)


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH
    )
    email: EmailStr
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        examples=['string1'],
    )
    full_name: str | None = Field(
        default=None,
        min_length=FULL_NAME_MIN_LENGTH,
        max_length=FULL_NAME_MAX_LENGTH,
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return validate_username_value(v, USERNAME_RE)

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        return validate_full_name_value(v)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return validate_password_value(v)


class TokenType(StrEnum):
    ACCESS = 'access'
    REFRESH = 'refresh'


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

    @model_validator(mode='after')
    def validate_tokens(self) -> TokenPair:
        if not self.access_token or not self.refresh_token:
            raise ValueError('Пустые токены недопустимы')
        if (self.token_type or 'bearer').casefold() != 'bearer':
            raise ValueError("token_type должен быть 'bearer'")
        self.token_type = 'bearer'
        return self


class TokenPayload(BaseModel):
    """
    Поля:
    - sub: идентификатор субъекта (обычно user_id)
    - exp: момент истечения токена (Unix timestamp)
    - iat: момент выпуска токена
    - jti: идентификатор токена (для трекинга/ревокации)
    - type: тип токена (access/refresh)
    - scope: необязательное поле с правами/ролями
    """

    sub: str
    exp: int
    iat: int
    jti: str
    type: TokenType
    scope: str | None = None

    @model_validator(mode='after')
    def validate_payload(self) -> TokenPayload:
        if not self.sub or not self.sub.strip():
            raise ValueError('sub обязателен')
        if not self.jti or not self.jti.strip():
            raise ValueError('jti обязателен')
        if self.exp <= 0 or self.iat <= 0:
            raise ValueError('exp и iat должны быть положительными')
        if self.exp <= self.iat:
            raise ValueError('exp должен быть больше iat')
        return self


class RefreshRequest(BaseModel):
    refresh_token: str


class RevokeRequest(BaseModel):
    """Запрос на отзыв (ревокацию) refresh-токена."""

    refresh_token: str


class AuthUser(UserSchema):
    model_config = ConfigDict(from_attributes=True, title='AuthUser')


def to_auth_user(user: UserSchema | object) -> AuthUser:
    return AuthUser.model_validate(user)


class AuthResponse(BaseModel):
    user: AuthUser
    tokens: TokenPair
    issued_at: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    message: str
