from dataclasses import dataclass

from backend.core.dto import AbstractDTO


@dataclass
class InviteDTO(AbstractDTO):
    invited_user_id: str | None
    invitee_user_id: str
