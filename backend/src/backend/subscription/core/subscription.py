from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.core.entity import AbstractEntity
from backend.core.utils import generate_uuid, get_current_time


class InvalidSubscriptionDataError(Exception):
    ...


@dataclass
class Subscription(AbstractEntity):
    tariff_id: str
    user_id: str
    paid: int
    active_from: datetime
    active_until: datetime | None = None

    @staticmethod
    def create(
        tariff_id: str,
        subscription_duration: int | None,
        paid: int,
        user_id: str,
        uuid: str | None = None,
    ) -> "Subscription":
        if subscription_duration is not None and subscription_duration <= 0:
            raise InvalidSubscriptionDataError(f"{subscription_duration=}")

        active_from = get_current_time()
        active_until = (
            None
            if subscription_duration is None
            else active_from + timedelta(hours=subscription_duration)
        )

        return Subscription(
            uuid=uuid or generate_uuid(),
            created_at=get_current_time(),
            deleted_at=None,
            tariff_id=tariff_id,
            user_id=user_id,
            paid=max(0, paid),
            active_from=active_from,
            active_until=active_until,
        )

    @property
    def is_active(self) -> bool:
        return (
            self.active_until is None
            or self.active_from <= get_current_time() < self.active_until
        )

    def update(self) -> "Subscription":
        raise NotImplementedError
