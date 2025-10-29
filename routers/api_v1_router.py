from fastapi import APIRouter

from apps.auth.routers import auth_router
from apps.project.routers import external_router, projects_router
from apps.user.routers import users_router

api_v1 = APIRouter(prefix='/api/v1')

for router in (auth_router, users_router, projects_router, external_router):
    api_v1.include_router(router)
