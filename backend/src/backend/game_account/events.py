from dataclasses import dataclass
from datetime import datetime

from backend.core.event import AbstractEvent


@dataclass
class GameAccountReadyForProcessingEvent(AbstractEvent):
    game_account_id: str


@dataclass
class UpdateGameAccountEvent(AbstractEvent):
    game_account_id: str
    balance: int | None
    is_invalid: bool | None
    last_login_at: datetime | None
