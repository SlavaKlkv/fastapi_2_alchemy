from fastapi import APIRouter

from apps.user.routers import users_router

api_v1 = APIRouter(prefix='/api/v1')

api_v1.include_router(users_router)
