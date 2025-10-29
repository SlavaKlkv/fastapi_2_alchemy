from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.project.schemas import (
    ProjectCreate,
    ProjectDeleteResponse,
    ProjectRead,
    ProjectsPage,
    ProjectUpdate,
)
from apps.project.services import ProjectService, fetch_external_posts
from apps.project.types import OrderField, ProjectStatus
from core.constants import PAGE_DEFAULT, PER_PAGE_DEFAULT, PER_PAGE_MAX
from core.database import get_async_session
from core.security import current_subject

projects_router = APIRouter(
    prefix='/projects',
    tags=['projects'],
    dependencies=[Depends(current_subject)],
)

external_router = APIRouter(prefix='/external', tags=['external'])


async def get_service(
    session: AsyncSession = Depends(get_async_session),
) -> ProjectService:
    return ProjectService(session)


@projects_router.get('/{project_id}', response_model=ProjectRead)
async def get_project(
    project_id: int,
    service: ProjectService = Depends(get_service),
) -> ProjectRead:
    return await service.get_one(project_id)


@projects_router.get('/', response_model=ProjectsPage)
async def list_projects(
    service: ProjectService = Depends(get_service),
    page: int = Query(PAGE_DEFAULT, ge=1),
    per_page: int = Query(PER_PAGE_DEFAULT, ge=1, le=PER_PAGE_MAX),
    status: ProjectStatus | None = Query(None),
    person_id: int | None = Query(None),
    order_by: OrderField = Query('create_time'),
    desc: bool = Query(True),
) -> ProjectsPage:
    return await service.list_projects(
        page=page,
        per_page=per_page,
        status=status,
        person_id=person_id,
        order_by=order_by,
        desc=desc,
    )


@projects_router.post(
    '/', response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
async def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_service),
) -> ProjectRead:
    return await service.create_one(payload)


@projects_router.post(
    '/bulk',
    response_model=List[ProjectRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_projects_bulk(
    payloads: List[ProjectCreate],
    service: ProjectService = Depends(get_service),
) -> List[ProjectRead]:
    return await service.create_many(payloads)


@projects_router.patch('/{project_id}', response_model=ProjectRead)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    service: ProjectService = Depends(get_service),
) -> ProjectRead:
    return await service.update_one(project_id, payload)


@projects_router.delete('/{project_id}', response_model=ProjectDeleteResponse)
async def delete_project(
    project_id: int,
    service: ProjectService = Depends(get_service),
) -> ProjectDeleteResponse:
    return await service.delete_one(project_id)


@external_router.get('/posts', summary='Получить посты из внешнего API')
async def get_external_posts(
    limit: int = Query(10, ge=1, le=100, description='Сколько постов вернуть'),
    page: int = Query(
        1,
        ge=1,
        description='Номер страницы',
    ),
    user_id: int | None = Query(None, description='Фильтр по автору (userId)'),
):
    return await fetch_external_posts(limit=limit, page=page, user_id=user_id)
