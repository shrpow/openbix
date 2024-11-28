from datetime import datetime

from beanie import Indexed
from typing_extensions import Annotated

from backend.game_account.core.status import Status
from backend.repository.mongo import AbstractMongoModel


class GameAccountModel(AbstractMongoModel):
    user_id: Annotated[str, Indexed()]
    status: Status
    last_login_at: datetime | None
    balance: int | None
    name: str
    auth_data: Annotated[str, Indexed()]
    proxy: str
    captcha_recognition_provider: str
    captcha_recognition_provider_api_key: str

    class Settings:
        name = "game_accounts"
        bson_encoders = {datetime: str}
        validate_on_save = True
