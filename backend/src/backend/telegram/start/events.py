from dataclasses import dataclass

from backend.core.event import AbstractEvent
from backend.i18n.language import Language
from backend.user.dto import UserDTO


@dataclass
class RegisterUserEvent(AbstractEvent):
    telegram_id: int
    invited_user_id: str | None
    language: Language


@dataclass
class SendMenuEvent(AbstractEvent):
    user: UserDTO
