from datetime import datetime

from backend.i18n.language import Language
from backend.repository.mongo import AbstractMongoModel
from backend.user.core.role import RoleName


class UserModel(AbstractMongoModel):
    uuid: str
    created_at: datetime | None
    deleted_at: datetime | None
    telegram_id: int
    language: Language
    role: RoleName
    balance: int

    class Settings:
        name = "users"
        bson_encoders = {datetime: str}
        validate_on_save = True
