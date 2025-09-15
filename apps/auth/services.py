from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt

from apps.auth.connector import (
    authenticate_credentials,
    create_user,
    get_user_by_username,
)
from apps.auth.schemas import TokenPair
from apps.user.schemas import User, UserCreate
from core.exceptions import InvalidCredentials, TokenExpired, TokenInvalid
from settings.settings import Setting

settings = Setting()


SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TTL_MIN: int = settings.ACCESS_TTL_MIN
REFRESH_TTL_DAYS: int = settings.REFRESH_TTL_DAYS

_REVOKED_REFRESH_JTI: set[str] = set()


class AuthService:
    def authenticate(self, login: str, password: str) -> User:
        user = authenticate_credentials(login, password)
        if not user:
            raise InvalidCredentials()
        return user

    def issue_tokens(self, user: User) -> TokenPair:
        now = datetime.now(timezone.utc)

        access = self._encode_token(
            sub=str(user.id),
            typ='access',
            iat=now,
            exp=now + timedelta(minutes=ACCESS_TTL_MIN),
        )
        refresh = self._encode_token(
            sub=str(user.id),
            typ='refresh',
            iat=now,
            exp=now + timedelta(days=REFRESH_TTL_DAYS),
        )
        return TokenPair(
            access_token=access, refresh_token=refresh, token_type='bearer'
        )

    def register(self, payload: UserCreate) -> User:
        user = get_user_by_username(payload.username)
        if user:
            raise InvalidCredentials('username занят')
        return create_user(payload)

    def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode_token(refresh_token)
        if payload.get('jti') in _REVOKED_REFRESH_JTI:
            raise TokenInvalid('refresh-токен отозван')
        if payload.get('type') != 'refresh':
            raise TokenInvalid('ожидался refresh-токен')

        sub: str = payload['sub']
        now = datetime.now(timezone.utc)

        access = self._encode_token(
            sub=sub,
            typ='access',
            iat=now,
            exp=now + timedelta(minutes=ACCESS_TTL_MIN),
        )
        new_refresh = self._encode_token(
            sub=sub,
            typ='refresh',
            iat=now,
            exp=now + timedelta(days=REFRESH_TTL_DAYS),
        )
        return TokenPair(
            access_token=access, refresh_token=new_refresh, token_type='bearer'
        )

    def revoke_refresh_token(self, token: str) -> None:
        """Ревокация refresh-токена."""

        payload = self._decode_token(token)
        if payload.get('type') != 'refresh':
            raise TokenInvalid('ожидался refresh-токен')
        jti = payload.get('jti')
        if jti:
            _REVOKED_REFRESH_JTI.add(jti)

    def decode_access(self, token: str) -> dict[str, Any]:
        payload = self._decode_token(token)
        if payload.get('type') != 'access':
            raise TokenInvalid('Ожидался access-токен')
        return payload

    def _encode_token(
        self, *, sub: str, typ: str, iat: datetime, exp: datetime
    ) -> str:
        payload: dict[str, Any] = {
            'sub': sub,
            'type': typ,  # тип токена: access/refresh
            'jti': uuid4().hex,  # уникальный id токена
            'iat': int(iat.timestamp()),
            'exp': int(exp.timestamp()),
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def _decode_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError as e:
            raise TokenExpired() from e
        except jwt.PyJWTError as e:
            raise TokenInvalid() from e
