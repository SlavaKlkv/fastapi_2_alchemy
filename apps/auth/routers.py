from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from apps.auth.schemas import (
    AuthResponse,
    LoginRequest,
    Message,
    RefreshRequest,
    RegisterRequest,
    RevokeRequest,
    TokenPair,
    to_auth_user,
)
from apps.auth.services import AuthService
from apps.user.schemas import User, UserCreate

auth_router = APIRouter(prefix='/auth', tags=['auth'])
_service = AuthService()


@auth_router.post(
    '/login',
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary='Вход через form-data (используется для Swagger Authorize)',
)
def login(form: OAuth2PasswordRequestForm = Depends()) -> TokenPair:
    """Авторизация через OAuth2PasswordRequestForm.
    Она фиксированно называет поле "username",
    но здесь оно может содержать username или email.
    """

    universal_login = form.username
    user = _service.authenticate(universal_login, form.password)
    return _service.issue_tokens(user)


@auth_router.post(
    '/login_json',
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary='Вход по JSON: username/email + password и '
    'получение access, refresh токенов',
)
def login_json(body: LoginRequest) -> AuthResponse:
    user = _service.authenticate(body.login, body.password)
    tokens = _service.issue_tokens(user)
    return AuthResponse(user=to_auth_user(user), tokens=tokens)


@auth_router.post(
    '/register',
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary='Регистрация пользователя',
)
def register(payload: RegisterRequest) -> User:
    user_payload = UserCreate(**payload.model_dump())
    return _service.register(user_payload)


@auth_router.post(
    '/refresh',
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
    summary='Обновление токенов по refresh',
)
def refresh(body: RefreshRequest) -> TokenPair:
    return _service.refresh(body.refresh_token)


@auth_router.post(
    '/logout',
    response_model=Message,
    summary='Отзыв токена',
    description='Аннулирует refresh-токен, делая его недействительным.',
)
def revoke_token(request: RevokeRequest) -> Message:
    token = request.refresh_token
    _service.revoke_refresh_token(token)
    return Message(message='refresh-токен отозван')
