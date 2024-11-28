from datetime import datetime

from beanie import Indexed
from typing_extensions import Annotated

from backend.repository.mongo import AbstractMongoModel


class InviteModel(AbstractMongoModel):
    invited_user_id: Annotated[str | None, Indexed()]
    invitee_user_id: str

    class Settings:
        name = "invites"
        bson_encoders = {datetime: str}
        validate_on_save = True
