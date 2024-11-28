from dataclasses import dataclass
from datetime import datetime

from backend.core.dto import AbstractDTO
from backend.game_account.core.status import Status


@dataclass
class GameAccountDTO(AbstractDTO):
    user_id: str
    status: Status
    last_login_at: datetime | None
    balance: int | None
    name: str
    auth_data: str
    proxy: str
    captcha_recognition_provider: str
    captcha_recognition_provider_api_key: str
