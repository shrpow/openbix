from dataclasses import dataclass

from backend.core.event import AbstractEvent


@dataclass
class EventSentEvent(AbstractEvent):
    ...
