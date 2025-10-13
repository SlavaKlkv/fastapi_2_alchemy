from __future__ import annotations

from fastapi import status
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.exceptions import (
    IntegrityConflictException,
    ProjectNotFoundException,
    UserAlreadyExistsException,
    UserNotFoundException,
    _json_error,
)


class DBErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)

        except (UserNotFoundException, ProjectNotFoundException) as exc:
            return _json_error(status.HTTP_404_NOT_FOUND, str(exc.detail))

        except (
            UserAlreadyExistsException,
            IntegrityConflictException,
        ) as exc:
            return _json_error(status.HTTP_409_CONFLICT, str(exc.detail))

        except IntegrityError as exc:
            code = getattr(getattr(exc, 'orig', None), 'pgcode', None)

            http_status = status.HTTP_400_BAD_REQUEST
            message = 'Нарушение целостности данных'

            if code == '23505':
                http_status = status.HTTP_409_CONFLICT
                message = 'Нарушение уникальности'
            elif code == '23503':
                http_status = status.HTTP_400_BAD_REQUEST
                message = 'Нарушение внешнего ключа'
            elif code == '23502':
                http_status = status.HTTP_400_BAD_REQUEST
                message = 'Обязательное поле не заполнено'
            elif code == '23514':
                http_status = status.HTTP_400_BAD_REQUEST
                message = 'Нарушение ограничения CHECK'

            return _json_error(http_status, message)

        except DBAPIError:
            return _json_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                'Ошибка базы данных',
            )

        except Exception:
            return _json_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                'Произошла непредвиденная ошибка',
            )
