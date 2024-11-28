from datetime import datetime

from beanie import Indexed
from typing_extensions import Annotated

from backend.repository.mongo import AbstractMongoModel


class SubscriptionModel(AbstractMongoModel):
    tariff_id: str
    user_id: Annotated[str, Indexed()]
    paid: int
    active_from: datetime
    active_until: datetime | None = None

    class Settings:
        name = "subscriptions"
        bson_encoders = {datetime: str}
        validate_on_save = True
