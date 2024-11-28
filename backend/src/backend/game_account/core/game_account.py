from dataclasses import dataclass
from datetime import datetime

from backend.core.entity import AbstractEntity
from backend.core.utils import generate_uuid, get_current_time
from backend.game_account.core.auth_data import AuthData
from backend.game_account.core.captcha_recognition_provider_api_key import (
    CaptchaRecognitionProviderApiKey,
)
from backend.game_account.core.name import Name
from backend.game_account.core.proxy import Proxy
from backend.game_account.core.status import Status


@dataclass
class GameAccount(AbstractEntity):
    user_id: str
    status: Status
    last_login_at: datetime | None
    balance: int | None
    name: str
    auth_data: str
    proxy: str
    captcha_recognition_provider: str
    captcha_recognition_provider_api_key: str

    @staticmethod
    def create(
        user_id: str,
        name: str,
        full_url: str,
        proxy: str,
        captcha_recognition_provider_api_key: str,
        uuid: str | None = None,
    ) -> "GameAccount":
        normalized_proxy = Proxy.from_string(proxy=proxy)
        normalized_auth_data = AuthData.from_string(full_url=full_url)
        normalized_name = Name.from_string(name=name)
        normalized_captcha_recognition_provider_api_key = (
            CaptchaRecognitionProviderApiKey.from_string(
                api_key=captcha_recognition_provider_api_key
            )
        )

        return GameAccount(
            uuid=uuid or generate_uuid(),
            created_at=get_current_time(),
            deleted_at=None,
            user_id=user_id,
            status=Status.ACTIVE,
            last_login_at=None,
            balance=None,
            name=normalized_name.name,
            auth_data=normalized_auth_data.auth_data,
            proxy=normalized_proxy.as_string(),
            captcha_recognition_provider="twocaptcha",
            captcha_recognition_provider_api_key=normalized_captcha_recognition_provider_api_key.api_key,
        )

    def update(
        self,
        status: Status | None,
        last_login_at: datetime | None,
        balance: int | None = None,
    ) -> "GameAccount":
        if status is not None:
            self.status = status

        if last_login_at is not None:
            self.last_login_at = last_login_at

        if balance is not None:
            self.balance = balance

        return self
