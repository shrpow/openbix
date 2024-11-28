from dataclasses import dataclass
from datetime import datetime

from backend.core.dto import AbstractDTO


@dataclass
class SubscriptionDTO(AbstractDTO):
    tariff_id: str
    user_id: str
    paid: int
    active_from: datetime
    active_until: datetime | None = None
