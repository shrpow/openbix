from dataclasses import dataclass

from backend.core.entity import AbstractEntity
from backend.core.utils import generate_uuid, get_current_time


@dataclass
class Invite(AbstractEntity):
    invited_user_id: str | None  # one who invited
    invitee_user_id: str  # one who is invited

    @staticmethod
    def create(
        invited_user_id: str | None,
        invitee_user_id: str,
        uuid: str | None = None,
    ) -> "Invite":
        return Invite(
            uuid=uuid or generate_uuid(),
            created_at=get_current_time(),
            deleted_at=None,
            invited_user_id=invited_user_id,
            invitee_user_id=invitee_user_id,
        )

    def update(self) -> "Invite":
        raise NotImplementedError
