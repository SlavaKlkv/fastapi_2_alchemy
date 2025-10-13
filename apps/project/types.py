from enum import Enum
from typing import Literal


class ProjectStatus(str, Enum):
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'


OrderField = Literal['create_time', 'start_time', 'complete_time']
