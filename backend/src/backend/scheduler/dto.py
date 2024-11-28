from dataclasses import dataclass
from typing import Callable

from backend.core.dto import AbstractDTO


@dataclass
class SchedulerJobDTO(AbstractDTO):
    function: Callable
    kwargs: dict
    interval: int
    jitter: int
