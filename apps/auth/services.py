from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.connector import (
    authenticate_credentials,
    create_user,
    get_user_by_username,
)
from apps.auth.schemas import TokenPair
from apps.user.schemas import User, UserCreate
from core.exceptions import InvalidCredentials, TokenExpired, TokenInvalid
from settings.settings import settings

SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TTL_MIN: int = settings.ACCESS_TTL_MIN
REFRESH_TTL_DAYS: int = settings.REFRESH_TTL_DAYS


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------- AUTH -------------------------

    async def authenticate(self, login: str, password: str) -> User:
        user = await authenticate_credentials(login, password, self.session)
        if not user:
            raise InvalidCredentials()
        return user

    async def register(self, payload: UserCreate) -> User:
        existing = await get_user_by_username(payload.username, self.session)
        if existing:
            raise InvalidCredentials('username занят')
        return await create_user(payload, self.session)

    # ------------------------- TOKENS -------------------------

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

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode_token(refresh_token)
        if payload.get('type') != 'refresh':
            raise TokenInvalid('ожидался refresh-токен')
        jti = payload.get('jti')
        if not jti or await self._is_refresh_revoked(jti):
            raise TokenInvalid('refresh-токен отозван')

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

    async def revoke_refresh_token(self, token: str) -> None:
        """Ревокация refresh-токена."""
        payload = self._decode_token(token)
        if payload.get('type') != 'refresh':
            raise TokenInvalid('ожидался refresh-токен')
        jti = payload.get('jti')
        if jti:
            await self._revoke_jti(jti)
            await self.session.commit()

    async def _is_refresh_revoked(self, jti: str) -> bool:
        query = text('SELECT 1 FROM auth_revoked_tokens WHERE jti = :jti')
        result = await self.session.execute(query, {'jti': jti})
        return result.scalar() is not None

    async def _revoke_jti(self, jti: str) -> None:
        query = text(
            'INSERT INTO auth_revoked_tokens (jti, revoked_at)'
            'VALUES (:jti, NOW()) ON CONFLICT DO NOTHING'
        )
        await self.session.execute(query, {'jti': jti})

    def decode_access(self, token: str) -> dict[str, Any]:
        payload = self._decode_token(token)
        if payload.get('type') != 'access':
            raise TokenInvalid('Ожидался access-токен')
        return payload

    # ------------------------- JWT utils -------------------------

    def _encode_token(
        self, *, sub: str, typ: str, iat: datetime, exp: datetime
    ) -> str:
        payload: dict[str, Any] = {
            'sub': sub,
            'type': typ,
            'jti': uuid4().hex,
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
