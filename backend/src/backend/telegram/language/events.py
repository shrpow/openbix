from dataclasses import dataclass

from backend.core.event import AbstractEvent
from backend.i18n.language import Language
from backend.user.dto import UserDTO


@dataclass
class UpdateUserLanguageEvent(AbstractEvent):
    user: UserDTO
    language: Language
