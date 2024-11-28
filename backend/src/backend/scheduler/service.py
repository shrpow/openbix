from typing import Type

from apscheduler.jobstores.memory import MemoryJobStore  # type: ignore
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from backend.core.utils import get_current_time
from backend.scheduler.core.job import SchedulerJob
from backend.scheduler.dto import SchedulerJobDTO


class SchedulerService:
    __scheduler: Type[AsyncIOScheduler]

    def __init__(self) -> None:
        self.__scheduler = AsyncIOScheduler(jobstores={"default": MemoryJobStore()})
        self.__scheduler.start()

    async def schedule_job(self, job: SchedulerJob) -> None:  # TODO entity is not ok
        self.__scheduler.add_job(
            **({"next_run_time": get_current_time()} if job.run_immediately else {}),
            func=job.function,
            trigger=IntervalTrigger(seconds=job.interval, jitter=job.jitter),
            kwargs=job.kwargs,
            id=job.uuid,
            coalesce=True,
            max_instances=1,
            replace_existing=True,
        )

    async def remove_job(self, job: SchedulerJobDTO) -> None:
        self.__scheduler.remove_job(job_id=job.uuid)
