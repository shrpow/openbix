from dataclasses import dataclass
from datetime import datetime


@dataclass
class AbstractDTO:
    uuid: str
    created_at: datetime | None
    deleted_at: datetime | None
