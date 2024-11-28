from dataclasses import dataclass
from typing import Callable

from backend.core.entity import AbstractEntity
from backend.core.utils import generate_uuid, get_current_time


@dataclass
class SchedulerJob(AbstractEntity):
    function: Callable
    kwargs: dict
    interval: int
    jitter: int
    run_immediately: bool

    @staticmethod
    def create(
        function: Callable,
        kwargs: dict,
        run_immediately: bool,
        interval: int = 1 * 60 * 60,
        jitter: int = 2 * 60 * 60,
        uuid: str | None = None,
    ) -> "SchedulerJob":
        return SchedulerJob(
            uuid=uuid or generate_uuid(),
            created_at=get_current_time(),
            deleted_at=None,
            function=function,
            kwargs=kwargs,
            run_immediately=run_immediately,
            interval=interval,
            jitter=jitter,
        )

    def update(self, *args, **kwargs) -> AbstractEntity:
        raise NotImplementedError
