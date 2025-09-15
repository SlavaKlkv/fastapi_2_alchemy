from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from apps.auth.services import AuthService

EXCLUDE_PATHS: set[str] = {
    '/docs',
    '/openapi.json',
    '/redoc',
    '/health',
    '/favicon.ico',
}
EXCLUDE_PREFIXES: tuple[str, ...] = ('/api/v1/auth',)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT-проверка заголовка Authorization: Bearer <access_token>."""

    def __init__(self, app):
        super().__init__(app)
        self._auth = AuthService()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in EXCLUDE_PATHS or any(
            path.startswith(p) for p in EXCLUDE_PREFIXES
        ):
            return await call_next(request)

        if request.method == 'OPTIONS':
            return await call_next(request)

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JSONResponse(
                {'detail': 'Not authenticated'}, status_code=401
            )

        token = auth_header.removeprefix('Bearer ').strip()
        payload = self._auth.decode_access(token)
        request.state.sub = payload.get('sub')

        return await call_next(request)
