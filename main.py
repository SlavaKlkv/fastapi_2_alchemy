from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware import Middleware

from core.exceptions import init_exception_handlers
from core.logging_setup import logger
from core.middleware.exc_middleware import DBErrorMiddleware
from core.middleware.jwt_middleware import JWTAuthMiddleware
from routers.api_v1_router import api_v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('app_started')
    yield


middleware = [
    Middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    ),
    Middleware(DBErrorMiddleware),  # type: ignore[arg-type]
    Middleware(JWTAuthMiddleware),  # type: ignore[arg-type]
]


app = FastAPI(
    title='User API',
    version='2.0.0',
    description='Приложение для управления пользователями и проектами '
    'со слоистой архитектурой и JWT-аутентификацией.',
    middleware=middleware,
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

init_exception_handlers(app)

app.include_router(api_v1)


@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok'}
