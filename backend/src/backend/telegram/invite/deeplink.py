from aiogram import Bot
from aiogram.utils.deep_linking import create_start_link
from pydantic import BaseModel
from pydantic.types import UUID4


class DeeplinkPayload(BaseModel):
    i: UUID4


async def create_deeplink(bot: Bot, payload: DeeplinkPayload) -> str:
    return await create_start_link(
        bot=bot, payload=payload.model_dump_json(), encode=True
    )
