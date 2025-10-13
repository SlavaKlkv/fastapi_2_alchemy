from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.project.models import Project
from apps.project.schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectsPage,
    ProjectUpdate,
)
from apps.project.types import OrderField
from core.constants import PAGE_DEFAULT, PER_PAGE_DEFAULT, PER_PAGE_MAX


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --------------------------- helpers ---------------------------

    @staticmethod
    def _to_schema(obj: Project) -> ProjectRead:
        return ProjectRead.model_validate(obj)

    @staticmethod
    def _apply_filters(
        stmt: Select[tuple[Project]],
        *,
        status: str | None,
        person_id: int | None,
    ) -> Select[tuple[Project]]:
        """
        SQL:
        WHERE (:status IS NULL OR projects.status = :status)
          AND (:person_id IS NULL OR
            projects.person_in_charge = :person_id);
        """
        if status:
            stmt = stmt.where(Project.status == status)
        if person_id:
            stmt = stmt.where(Project.person_in_charge == person_id)
        return stmt

    @staticmethod
    def _apply_order(
        stmt: Select[tuple[Project]], *, order_by: OrderField, desc: bool
    ) -> Select[tuple[Project]]:
        col = {
            'create_time': Project.create_time,
            'start_time': Project.start_time,
            'complete_time': Project.complete_time,
        }.get(order_by, Project.create_time)
        return stmt.order_by(col.desc() if desc else col.asc())

    # --------------------------- queries ---------------------------

    async def get_by_id(self, project_id: int) -> ProjectRead | None:
        """
        SQL:
        SELECT p.*
        FROM projects AS p
        WHERE p.id = :project_id
        LIMIT 1;
        """
        res = await self.session.execute(
            select(Project).where(Project.id == project_id).limit(1)
        )
        obj = res.scalar_one_or_none()
        return self._to_schema(obj) if obj else None

    async def list_paginated(
        self,
        *,
        page: int = PAGE_DEFAULT,
        per_page: int = PER_PAGE_DEFAULT,
        status: str | None = None,
        person_id: int | None = None,
        order_by: OrderField = 'create_time',
        desc: bool = True,
    ) -> ProjectsPage:
        """
        SQL:
        -- страница
        SELECT p.*
        FROM projects AS p
        WHERE (:status IS NULL OR p.status = :status)
          AND (:person_id IS NULL OR p.person_in_charge = :person_id)
        ORDER BY CASE WHEN :order_by = 'create_time'
                      THEN p.create_time
                      END DESC,
                 CASE WHEN :order_by = 'start_time'
                      THEN p.start_time
                      END DESC,
                 CASE WHEN :order_by = 'complete_time'
                      THEN p.complete_time
                      END DESC
        LIMIT :per_page OFFSET :offset;

        -- общее количество
        SELECT COUNT(*)
        FROM projects AS p
        WHERE (:status IS NULL OR p.status = :status)
          AND (:person_id IS NULL OR p.person_in_charge = :person_id);
        """
        per_page = min(per_page, PER_PAGE_MAX)

        stmt = select(Project)
        stmt = self._apply_filters(stmt, status=status, person_id=person_id)
        stmt = self._apply_order(stmt, order_by=order_by, desc=desc)

        offset = max(page - 1, 0) * per_page
        page_res = await self.session.execute(
            stmt.offset(offset).limit(per_page)
        )
        items: Sequence[Project] = page_res.scalars().all()

        count_stmt = select(func.count()).select_from(
            stmt.order_by(None).limit(None).offset(None).subquery()
        )
        total = (await self.session.execute(count_stmt)).scalar_one()

        has_prev = page > 1
        has_next = offset + len(items) < total

        return ProjectsPage(
            items=[self._to_schema(i) for i in items],
            page=page,
            per_page=per_page,
            total_count=int(total),
            has_prev=has_prev,
            has_next=has_next,
        )

    # --------------------------- mutations ---------------------------

    async def create_one(self, payload: ProjectCreate) -> ProjectRead:
        """
        SQL:
        INSERT INTO projects (
            name,
            status,
            create_time,
            start_time,
            complete_time,
            description,
            person_in_charge
        )
        VALUES (
            :name,
            :status,
            :create_time,
            :start_time,
            :complete_time,
            :description,
            :person_in_charge
        )
        RETURNING *;
        """
        obj = Project(**payload.model_dump())
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return self._to_schema(obj)

    async def create_many(
        self, payloads: Iterable[ProjectCreate]
    ) -> list[ProjectRead]:
        """
        SQL (семантически; выполняется в цикле ORM):
        INSERT INTO projects (...columns...)
        VALUES (...values...)
        RETURNING *;  -- для каждой записи
        """
        created: list[ProjectRead] = []
        for p in payloads:
            obj = Project(**p.model_dump())
            self.session.add(obj)
            await self.session.flush()
            await self.session.refresh(obj)
            created.append(self._to_schema(obj))
        return created

    async def update_one(
        self, project_id: int, payload: ProjectUpdate
    ) -> ProjectRead | None:
        """
        SQL:
        UPDATE projects
        SET
            name = COALESCE(:name, name),
            status = COALESCE(:status, status),
            start_time = COALESCE(:start_time, start_time),
            complete_time = COALESCE(:complete_time, complete_time),
            description = COALESCE(:description, description),
            person_in_charge = COALESCE(:person_in_charge, person_in_charge)
        WHERE id = :project_id
        RETURNING *;
        """
        res = await self.session.execute(
            select(Project).where(Project.id == project_id).limit(1)
        )
        obj = res.scalar_one_or_none()
        if obj is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        data.pop('create_time', None)
        for k, v in data.items():
            setattr(obj, k, v)

        await self.session.flush()
        await self.session.refresh(obj)
        return self._to_schema(obj)

    async def delete_one(self, project_id: int) -> ProjectRead | None:
        """
        SQL:
        DELETE FROM projects
        WHERE id = :project_id
        RETURNING *;  -- эмулируется через возврат ранее загруженного объекта
        """
        res = await self.session.execute(
            select(Project).where(Project.id == project_id).limit(1)
        )
        obj = res.scalar_one_or_none()
        if obj is None:
            return None
        await self.session.delete(obj)
        return self._to_schema(obj)

    async def exists_by_name(self, name: str) -> bool:
        """Проверка существования проекта с таким именем.
        SQL:
        SELECT COUNT(*)
        FROM projects
        WHERE name = :name;
        """
        stmt = (
            select(func.count())
            .select_from(Project)
            .where(Project.name == name)
        )
        result = await self.session.execute(stmt)
        count = result.scalar_one_or_none() or 0
        return count > 0
