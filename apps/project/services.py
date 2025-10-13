from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from apps.project.repository import ProjectRepository
from apps.project.schemas import (
    ProjectCreate,
    ProjectDeleteResponse,
    ProjectRead,
    ProjectsPage,
    ProjectUpdate,
)
from apps.project.types import OrderField
from apps.user.models import User
from core.exceptions import (
    IntegrityConflictException,
    ProjectNotFoundException,
)

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProjectRepository(session)

    # --------------------------- queries ---------------------------

    async def get_one(self, project_id: int) -> ProjectRead:
        project = await self.repo.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundException(project_id)
        return project

    async def list_projects(
        self,
        *,
        page: int,
        per_page: int,
        status: str | None = None,
        person_id: int | None = None,
        order_by: OrderField = 'create_time',
        desc: bool = True,
    ) -> ProjectsPage:
        return await self.repo.list_paginated(
            page=page,
            per_page=per_page,
            status=status,
            person_id=person_id,
            order_by=order_by,
            desc=desc,
        )

    # --------------------------- mutations ---------------------------

    async def create_one(self, payload: ProjectCreate) -> ProjectRead:
        if await self.repo.exists_by_name(payload.name):
            raise IntegrityConflictException(
                'Проект с таким именем уже существует'
            )
        if payload.person_in_charge is not None:
            user = await self.session.get(User, payload.person_in_charge)
            if user is None:
                raise IntegrityConflictException(
                    'Связанный пользователь (person_id) не найден'
                )

        project = await self.repo.create_one(payload)
        await self.session.commit()
        return project

    async def create_many(
        self, payloads: Iterable[ProjectCreate]
    ) -> list[ProjectRead]:
        projects = await self.repo.create_many(list(payloads))
        await self.session.commit()
        return projects

    async def update_one(
        self, project_id: int, payload: ProjectUpdate
    ) -> ProjectRead:
        project = await self.repo.update_one(project_id, payload)
        if project is None:
            raise ProjectNotFoundException(project_id)
        await self.session.commit()
        return project

    async def delete_one(self, project_id: int) -> ProjectDeleteResponse:
        project = await self.repo.delete_one(project_id)
        if project is None:
            raise ProjectNotFoundException(project_id)
        await self.session.commit()
        return project
