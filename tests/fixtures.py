from datetime import UTC, datetime

import pytest

from apps.project.models import Project, ProjectStatus
from apps.user.models import User


@pytest.fixture
async def user(test_session):
    user = User(
        username='test_user',
        email='test_user@example.com',
        full_name='Тестовый пользователь',
        hashed_password='hash123',
        disabled=False,
    )
    test_session.add(user)
    await test_session.flush()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def users(test_session):
    users = [
        User(
            username='alice',
            email='alice@example.com',
            full_name='Alice',
            hashed_password='hash1',
            disabled=False,
        ),
        User(
            username='bob',
            email='bob@example.com',
            full_name='Bob',
            hashed_password='hash2',
            disabled=False,
        ),
        User(
            username='carol',
            email='carol@example.com',
            full_name='Carol',
            hashed_password='hash3',
            disabled=False,
        ),
    ]
    test_session.add_all(users)
    await test_session.flush()
    for u in users:
        await test_session.refresh(u)
    return users


@pytest.fixture
async def another_user(test_session):
    user = User(
        username='other_user',
        email='other@example.com',
        full_name='Другой пользователь',
        hashed_password='hash456',
        disabled=False,
    )
    test_session.add(user)
    await test_session.flush()
    await test_session.refresh(user)
    return user


@pytest.fixture
async def project(test_session, user):
    project = Project(
        name='Тестовый проект',
        description='Описание тестового проекта',
        status=ProjectStatus.NEW,
        person_in_charge=user.id,
        start_time=None,
        complete_time=None,
    )
    test_session.add(project)
    await test_session.flush()
    await test_session.refresh(project)
    return project


@pytest.fixture
async def projects(test_session, users):
    projects = [
        Project(
            name='Проект А',
            description='Описание проекта А',
            status=ProjectStatus.NEW,
            person_in_charge=users[0].id,
        ),
        Project(
            name='Проект Б',
            description='Описание проекта Б',
            status=ProjectStatus.IN_PROGRESS,
            person_in_charge=users[1].id,
            start_time=datetime.now(UTC),
        ),
        Project(
            name='Проект В',
            description='Описание проекта В',
            status=ProjectStatus.COMPLETED,
            person_in_charge=users[2].id,
            start_time=datetime.now(UTC),
            complete_time=datetime.now(UTC),
        ),
    ]
    test_session.add_all(projects)
    await test_session.flush()
    for p in projects:
        await test_session.refresh(p)
    return projects
