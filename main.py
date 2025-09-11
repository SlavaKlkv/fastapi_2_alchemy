from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.exceptions import init_exception_handlers
from routers.api_v1_router import api_v1


app = FastAPI(
    title='User API',
    version='1.0.0',
    description='Приложение для управления пользователями '
    'со слоистой архитектурой и JWT-аутентификацией.',
)

init_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_v1)


@app.get('/health', tags=['system'])
def health():
    return {'status': 'ok'}
