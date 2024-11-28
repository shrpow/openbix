from dataclasses import dataclass

from backend.core.event import AbstractEvent
from backend.subscription.dto import SubscriptionDTO
from backend.tariff.dto import TariffDTO
from backend.user.dto import UserDTO


@dataclass
class SubscriptionCreatedEvent(AbstractEvent):
    issuer: UserDTO
    tariff: TariffDTO
    subscription: SubscriptionDTO
