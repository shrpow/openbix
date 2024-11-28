from dataclasses import dataclass

from backend.core.event import AbstractEvent


@dataclass
class NewInvitedUserEvent(AbstractEvent):
    invited_user_id: str | None
    invitee_user_id: str


@dataclass
class NewInviteEvent(AbstractEvent):
    ...


@dataclass
class WithdrawBalanceEvent(AbstractEvent):
    user_id: str
    amount: int


@dataclass
class AddInviteRewardEvent(AbstractEvent):
    user_id: str
    reward: int
