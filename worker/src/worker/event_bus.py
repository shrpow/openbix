import asyncio
import enum
from collections import defaultdict
from collections.abc import Coroutine
from typing import Any, Callable


class EventType(enum.StrEnum):
    ACCOUNT_BAN_DETECTED = enum.auto()
    STOP_WORK = enum.auto()
    NEW_TASK = enum.auto()


class EventBus:
    __recipients: dict[EventType, list[Callable[..., Coroutine]]]

    def __init__(self) -> None:
        self.__recipients = defaultdict(lambda: [])

    def on_event(self, event_type: EventType, callback: Callable) -> None:
        self.__recipients[event_type].append(callback)

    async def emit(self, event_type: EventType, payload: Any) -> None:
        for callback in self.__recipients.get(event_type, []):
            asyncio.create_task(callback(payload=payload))
