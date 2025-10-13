from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from apps.project.types import ProjectStatus
from core.constants import NAME_MAX_LENGTH
from core.database import Base


class Project(Base):
    """
    SQL schema:

    CREATE TABLE projects (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL,
        status VARCHAR(20)
          CHECK (status IN ('new', 'in_progress', 'completed')) DEFAULT 'new',
        create_time TIMESTAMP NOT NULL DEFAULT NOW(),
        start_time TIMESTAMP,
        complete_time TIMESTAMP,
        description TEXT,
        person_in_charge INTEGER REFERENCES users(id)
    );
    """

    __tablename__ = 'projects'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(NAME_MAX_LENGTH), unique=True, nullable=False
    )
    status: Mapped[ProjectStatus] = mapped_column(
        SqlEnum(ProjectStatus, name='project_status'),
        nullable=False,
        default=ProjectStatus.NEW,
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # автоматически ставит текущее время
    )
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    complete_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    description: Mapped[str | None] = mapped_column(Text)

    person_in_charge: Mapped[int | None] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL')
    )
    user = relationship('User', back_populates='projects')

    def __repr__(self) -> str:
        return (
            f'<Project(id={self.id}, name={self.name}, status={self.status})>'
        )
