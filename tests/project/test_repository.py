import pytest
from sqlalchemy import select

from apps.project.models import Project
from apps.project.repository import ProjectRepository
from apps.project.schemas import (
    ProjectCreate,
    ProjectRead,
    ProjectsPage,
    ProjectUpdate,
)
from core.constants import PER_PAGE_MAX


@pytest.fixture
def repo(test_session) -> ProjectRepository:
    return ProjectRepository(test_session)


@pytest.mark.database
class TestProjectRepository:
    async def test_get_by_id_found(
        self, repo: ProjectRepository, project: ProjectRead
    ):
        got = await repo.get_by_id(project.id)
        assert got is not None
        assert got.id == project.id
        assert got.name == project.name
        assert got.status == project.status
        assert got.description == project.description
        assert got.person_in_charge == project.person_in_charge

    async def test_get_by_id_not_found(self, repo: ProjectRepository):
        missing = await repo.get_by_id(999_999)
        assert missing is None

    async def test_list_paginated_basic(
        self, repo: ProjectRepository, projects: list[ProjectRead]
    ):
        page = await repo.list_paginated(
            page=1, per_page=2, order_by='create_time', desc=True
        )
        assert isinstance(page, ProjectsPage)
        assert page.page == 1
        assert page.per_page == 2
        assert page.total_count == len(projects)
        assert len(page.items) == 2
        assert page.has_prev is False
        assert page.has_next is True

        page2 = await repo.list_paginated(
            page=2, per_page=2, order_by='create_time', desc=True
        )
        assert page2.page == 2
        assert len(page2.items) == 1
        assert page2.has_prev is True
        assert page2.has_next is False

    async def test_list_paginated_filters(
        self, repo: ProjectRepository, projects: list[ProjectRead]
    ):
        status = projects[0].status
        page = await repo.list_paginated(status=status, per_page=10)
        assert all(item.status == status for item in page.items)
        pid = projects[0].person_in_charge
        page2 = await repo.list_paginated(person_id=pid, per_page=10)
        assert len(page2.items) >= 1
        assert all(item.person_in_charge == pid for item in page2.items)

    async def test_list_paginated_ordering(
        self, repo: ProjectRepository, projects: list[ProjectRead]
    ):
        page_asc = await repo.list_paginated(
            order_by='start_time', desc=False, per_page=10
        )
        starts = [p.start_time for p in page_asc.items]
        assert starts == sorted(starts, key=lambda x: (x is None, x))

        page_desc = await repo.list_paginated(
            order_by='complete_time', desc=True, per_page=10
        )
        completes = [p.complete_time for p in page_desc.items]
        dates_only = [d for d in completes if d is not None]
        assert dates_only == sorted(dates_only, reverse=True)

    async def test_list_paginated_caps_per_page(
        self, repo: ProjectRepository, projects: list[ProjectRead]
    ):
        requested = PER_PAGE_MAX + 100
        page = await repo.list_paginated(per_page=requested)
        assert page.per_page == min(requested, PER_PAGE_MAX)

    async def test_create_one(
        self, repo: ProjectRepository, test_session, project: ProjectRead
    ):
        payload = ProjectCreate(
            name=project.name + ' create',
            status=project.status,
            description=project.description,
            person_in_charge=project.person_in_charge,
        )
        created = await repo.create_one(payload)
        assert isinstance(created, ProjectRead)
        assert created.id is not None
        assert created.name == payload.name
        assert created.status == payload.status
        assert created.description == payload.description
        assert created.person_in_charge == payload.person_in_charge

        res = await test_session.execute(
            select(Project).where(Project.id == created.id)
        )
        db_obj = res.scalar_one_or_none()
        assert db_obj is not None
        assert db_obj.name == payload.name

    async def test_create_many(
        self,
        repo: ProjectRepository,
        test_session,
        projects: list[ProjectRead],
    ):
        payloads = [
            ProjectCreate(
                name=p.name + ' копия',
                status=p.status,
                description=p.description,
                person_in_charge=p.person_in_charge,
            )
            for p in projects
        ]
        created = await repo.create_many(payloads)
        assert isinstance(created, list) and len(created) == len(payloads)

        names = {p.name for p in payloads}
        res = await test_session.execute(
            select(Project.name).where(Project.name.in_(names))
        )
        db_names = set(res.scalars().all())
        assert db_names == names

    async def test_update_one(
        self, repo: ProjectRepository, test_session, project: ProjectRead
    ):
        upd = ProjectUpdate(
            status='in_progress',
            description='Обновлённое описание',
        )
        updated = await repo.update_one(project.id, upd)
        assert updated is not None
        assert updated.id == project.id
        assert updated.status == 'in_progress'
        assert updated.description == 'Обновлённое описание'

        res = await test_session.execute(
            select(Project).where(Project.id == project.id)
        )
        obj = res.scalar_one()
        assert obj.status == 'in_progress'
        assert obj.description == 'Обновлённое описание'

        not_found = await repo.update_one(
            999_999, ProjectUpdate(description='x')
        )
        assert not_found is None

    async def test_delete_one(
        self, repo: ProjectRepository, test_session, project: ProjectRead
    ):
        deleted = await repo.delete_one(project.id)
        assert deleted is not None
        assert deleted.id == project.id
        assert deleted.name == project.name
        assert deleted.status == project.status
        assert deleted.description == project.description
        assert deleted.person_in_charge == project.person_in_charge

        await test_session.flush()
        res = await test_session.execute(
            select(Project).where(Project.id == project.id)
        )
        assert res.scalar_one_or_none() is None

        again = await repo.delete_one(project.id)
        assert again is None

    async def test_exists_by_name(
        self, repo: ProjectRepository, project: ProjectRead
    ):
        assert await repo.exists_by_name(project.name) is True
        assert await repo.exists_by_name('non_existing_name') is False
