from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# ============================== Кастомные исключения =========================


class StoreError(HTTPException):
    """Базовая ошибка хранилища."""

    def __init__(
        self,
        detail: str = 'Ошибка хранилища',
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        super().__init__(status_code=status_code, detail=detail)


class StoreConnectionError(StoreError):
    """Ошибка подключения к хранилищу."""

    def __init__(self, detail: str = 'Не удалось подключиться к хранилищу'):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class StoreDataError(StoreError):
    """Ошибка целостности/формата данных в хранилище."""

    def __init__(self, detail: str = 'Некорректные данные в хранилище'):
        super().__init__(
            detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class UserNotFoundException(HTTPException):
    """Пользователь не найден."""

    def __init__(self, user_id: int | None = None):
        msg = (
            'Пользователь не найден'
            if user_id is None
            else f'Пользователь с ID {user_id} не найден'
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


class UserAlreadyExistsException(HTTPException):
    """Пользователь уже существует (конфликт уникальности)."""

    def __init__(self, field: str = 'username'):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Пользователь с таким {field} уже существует',
        )


# ============================== Регистрация обработчиков =====================


def _json_error(
    status_code: int, detail: str, *, errors: Any | None = None
) -> JSONResponse:
    payload: dict[str, Any] = {'detail': detail}
    if errors is not None:
        payload['errors'] = errors
    return JSONResponse(status_code=status_code, content=payload)


def init_exception_handlers(app):
    """
    Регистрирует глобальные обработчики исключений.
    Единый формат ошибок: {"detail": "...", "errors": [...] (опционально)}.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return _json_error(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request, exc: RequestValidationError
    ):
        return _json_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            'Некорректные данные запроса',
            errors=exc.errors(),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(
        request: Request, exc: ValidationError
    ):
        return _json_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            'Ошибка валидации данных',
            errors=exc.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ):
        return _json_error(exc.status_code, str(exc.detail))

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return _json_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'Произошла непредвиденная ошибка',
        )
