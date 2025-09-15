from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware

from core.exceptions import init_exception_handlers
from core.jwt_middleware import JWTAuthMiddleware
from routers.api_v1_router import api_v1

middleware = [
    Middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    ),
    Middleware(JWTAuthMiddleware),  # type: ignore[arg-type]
]

app = FastAPI(
    title='User API',
    version='1.0.0',
    description='Приложение для управления пользователями '
    'со слоистой архитектурой и JWT-аутентификацией.',
    middleware=middleware,
)

init_exception_handlers(app)

app.include_router(api_v1)


@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok'}
