from dataclasses import dataclass

from backend.core.entity import AbstractEntity
from backend.core.utils import generate_uuid, get_current_time
from backend.i18n.language import Language
from backend.user.core.role import RoleName


@dataclass
class User(AbstractEntity):
    telegram_id: int
    language: Language
    role: RoleName
    balance: int

    @staticmethod
    def create(
        telegram_id: int,
        language: Language = Language.EN,
        balance: int = 0,
        uuid: str | None = None,
    ) -> "User":
        return User(
            uuid=uuid or generate_uuid(),
            created_at=get_current_time(),
            deleted_at=None,
            telegram_id=telegram_id,
            language=language,
            role=RoleName.CUSTOMER,
            balance=balance,
        )

    def update(
        self,
        language: Language | None = None,
        role: RoleName | None = None,
        balance: int | None = None,
    ) -> "User":
        if language is not None:
            self.language = language

        if role is not None:
            self.role = role

        if balance is not None:
            self.balance = max(0, balance)

        return self
