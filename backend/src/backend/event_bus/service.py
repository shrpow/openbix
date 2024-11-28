import asyncio
from collections import defaultdict
from collections.abc import Coroutine
from typing import Callable, Type

from loguru import logger

from backend.core.event import AbstractEvent
from backend.core.utils import get_current_time
from backend.event_bus.events import EventSentEvent


class EventBusService:
    __recipients: dict[Type[AbstractEvent], list[Callable[..., Coroutine]]]

    def __init__(self) -> None:
        self.__recipients = defaultdict(list)

    def on_event(
        self, event_type: Type[AbstractEvent], callback: Callable[..., Coroutine]
    ) -> None:
        self.__recipients[event_type].append(callback)

    async def emit(self, event: AbstractEvent, send_metrics: bool = True) -> None:
        logger.debug(f"{event=}")

        if send_metrics:
            asyncio.create_task(
                self.emit(
                    event=EventSentEvent(created_at=get_current_time()),
                    send_metrics=False,
                )
            )

        for callback in self.__recipients[type(event)]:
            asyncio.create_task(callback(event=event))
