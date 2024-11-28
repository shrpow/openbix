import asyncio

from worker.config import Config
from worker.emq.service import ExternalMQService
from worker.event_bus import EventBus
from worker.task.service.service import TaskService

# TODO backoff, improve error handlers, fix Game Core entities naming, improve mappers


async def main() -> None:
    emq_service = ExternalMQService()
    asyncio.create_task(
        emq_service.start_listener(address=Config.EMQ_WORKER_BALANCER_OUTPUT_ADDRESS)
    )
    event_bus = EventBus()
    task_service = TaskService(event_bus=event_bus, emq_service=emq_service)
    await task_service.start_heartbeat()


if __name__ == "__main__":
    asyncio.run(main=main())
