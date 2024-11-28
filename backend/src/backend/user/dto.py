from dataclasses import dataclass

from backend.core.dto import AbstractDTO
from backend.i18n.language import Language
from backend.user.core.role import RoleName


@dataclass
class UserDTO(AbstractDTO):
    telegram_id: int
    language: Language
    role: RoleName
    balance: int
