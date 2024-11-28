from dataclasses import dataclass

from backend.core.event import AbstractEvent


@dataclass
class NewGameAccountTaskEvent(AbstractEvent):
    game_account_id: str


@dataclass
class SuccessTaskEvent(AbstractEvent):
    ...


@dataclass
class FailedTaskEvent(AbstractEvent):
    ...
