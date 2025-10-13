from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from apps.project.types import ProjectStatus
from core.constants import NAME_MAX_LENGTH


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=NAME_MAX_LENGTH)
    status: ProjectStatus = ProjectStatus.NEW
    description: str | None = None
    person_in_charge: int = 1


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    status: ProjectStatus | None = None
    start_time: datetime | None = None
    complete_time: datetime | None = None
    description: str | None = None
    person_in_charge: int | None = 1


class ProjectRead(ProjectBase):
    id: int
    create_time: datetime
    start_time: datetime | None
    complete_time: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ProjectsPage(BaseModel):
    items: List[ProjectRead]
    page: int
    per_page: int
    total_count: int
    has_prev: bool
    has_next: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectDeleteResponse(ProjectRead):
    deleted: bool = True
