import pytest
from sqlalchemy import select

from apps.project.models import Project
from apps.project.schemas import (
    ProjectCreate,
    ProjectDeleteResponse,
    ProjectRead,
    ProjectsPage,
    ProjectUpdate,
)
from apps.project.services import ProjectService
from core.exceptions import (
    IntegrityConflictException,
    ProjectNotFoundException,
)


@pytest.fixture
def project_service(test_session) -> ProjectService:
    return ProjectService(test_session)


@pytest.mark.services
class TestProjectService:
    async def test_get_one_ok(
        self, project_service: ProjectService, project: Project
    ):
        got = await project_service.get_one(project.id)
        assert isinstance(got, ProjectRead)
        assert got.id == project.id
        assert got.name == project.name
        assert got.status == project.status
        assert got.description == project.description
        assert got.person_in_charge == project.person_in_charge

    async def test_get_one_not_found_raises(
        self, project_service: ProjectService
    ):
        with pytest.raises(ProjectNotFoundException):
            await project_service.get_one(999_999)

    async def test_list_projects_basic(
        self, project_service: ProjectService, projects: list[Project]
    ):
        page = await project_service.list_projects(page=1, per_page=2)
        assert isinstance(page, ProjectsPage)
        assert page.page == 1
        assert page.per_page == 2
        assert page.total_count >= len(projects)
        assert len(page.items) == 2
        assert page.has_prev is False
        assert page.has_next is True

        page2 = await project_service.list_projects(page=2, per_page=2)
        assert page2.page == 2
        assert len(page2.items) == max(0, min(2, page.total_count - 2))
        assert page2.has_prev is True
        assert page2.has_next is False

    async def test_list_projects_filters_status(
        self, project_service: ProjectService, projects: list[Project]
    ):
        page = await project_service.list_projects(
            page=1, per_page=10, status='new'
        )
        assert all(p.status == 'new' for p in page.items)

    async def test_list_projects_filters_person(
        self, project_service: ProjectService, projects: list[Project]
    ):
        person_id = projects[0].person_in_charge
        page = await project_service.list_projects(
            page=1, per_page=10, person_id=person_id
        )
        assert len(page.items) >= 1
        assert all(p.person_in_charge == person_id for p in page.items)

    async def test_create_one_ok(
        self, project_service: ProjectService, project: Project, user
    ):
        payload = ProjectCreate(
            name=project.name + ' svc-create',
            status=project.status,
            description='Создано через сервис',
            person_in_charge=user.id,
        )
        created = await project_service.create_one(payload)
        assert isinstance(created, ProjectRead)
        assert created.name == payload.name
        assert created.status == payload.status
        assert created.description == payload.description
        assert created.person_in_charge == payload.person_in_charge

        # проверка в БД
        res = await project_service.session.execute(
            select(Project).where(Project.id == created.id)
        )
        assert res.scalar_one_or_none() is not None

    async def test_create_one_duplicate_name_raises(
        self, project_service: ProjectService, project: Project, user
    ):
        payload = ProjectCreate(
            name=project.name,  # дубликат
            status=project.status,
            description='дубль',
            person_in_charge=user.id,
        )
        with pytest.raises(IntegrityConflictException):
            await project_service.create_one(payload)

    async def test_create_one_person_not_found_raises(
        self, project_service: ProjectService, project: Project
    ):
        payload = ProjectCreate(
            name=project.name + ' svc-bad-user',
            status=project.status,
            description='ошибка person',
            person_in_charge=999_999,
        )
        with pytest.raises(IntegrityConflictException):
            await project_service.create_one(payload)

    async def test_create_many_ok(self, project_service: ProjectService, user):
        payloads = [
            ProjectCreate(
                name=f'svc-bulk-{i}',
                status='new',
                description=f'bulk {i}',
                person_in_charge=user.id,
            )
            for i in range(2)
        ]
        created = await project_service.create_many(payloads)
        assert isinstance(created, list)
        assert len(created) == 2
        assert [p.name for p in created] == [pl.name for pl in payloads]

        res = await project_service.session.execute(
            select(Project.name).where(
                Project.name.in_([pl.name for pl in payloads])
            )
        )
        assert set(res.scalars().all()) == {pl.name for pl in payloads}

    async def test_update_one_ok(
        self, project_service: ProjectService, project: Project
    ):
        upd = ProjectUpdate(
            status='in_progress',
            description='Обновлено сервисом',
        )
        updated = await project_service.update_one(project.id, upd)
        assert isinstance(updated, ProjectRead)
        assert updated.id == project.id
        assert updated.name == project.name  # имя не меняется
        assert updated.status == 'in_progress'
        assert updated.description == 'Обновлено сервисом'

        res = await project_service.session.execute(
            select(Project).where(Project.id == project.id)
        )
        obj = res.scalar_one()
        assert obj.status == 'in_progress'
        assert obj.description == 'Обновлено сервисом'
        assert obj.name == project.name

    async def test_update_one_not_found_raises(
        self, project_service: ProjectService
    ):
        with pytest.raises(ProjectNotFoundException):
            await project_service.update_one(
                999_999, ProjectUpdate(description='x')
            )

    async def test_delete_one_ok(
        self, project_service: ProjectService, project: Project
    ):
        deleted = await project_service.delete_one(project.id)
        assert isinstance(deleted, ProjectDeleteResponse)
        assert deleted.id == project.id
        assert deleted.name == project.name
        assert deleted.status == project.status
        assert deleted.description == project.description
        assert deleted.person_in_charge == project.person_in_charge
        assert deleted.deleted is True

        res = await project_service.session.execute(
            select(Project).where(Project.id == project.id)
        )
        assert res.scalar_one_or_none() is None

        with pytest.raises(ProjectNotFoundException):
            await project_service.delete_one(project.id)
