import enum
from dataclasses import dataclass
from datetime import datetime


class Status(enum.StrEnum):
    ACTIVE = enum.auto()
    INACTIVE = enum.auto()


@dataclass
class GameAccountDTO:
    uuid: str
    created_at: datetime | None
    deleted_at: datetime | None
    user_id: str
    status: Status
    last_login_at: datetime | None
    balance: int | None
    name: str
    auth_data: str
    proxy: str
