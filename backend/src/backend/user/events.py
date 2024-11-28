from dataclasses import dataclass

from backend.core.event import AbstractEvent


@dataclass
class UserBalanceAddBonusEvent(AbstractEvent):
    amount: int
