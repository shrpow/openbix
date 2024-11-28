import asyncio
import json

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message
from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.i18n.language import Language
from backend.telegram.invite.deeplink import DeeplinkPayload
from backend.telegram.start.events import RegisterUserEvent
from pydantic import ValidationError


class StartRouter(Router):
    __event_bus_service: EventBusService

    def __init__(self, event_bus_service: EventBusService) -> None:
        super().__init__()

        self.__event_bus_service = event_bus_service

        self.name = "Start"

        self.message.register(
            self.handle_command_start_deeplink,
            CommandStart(deep_link=True, deep_link_encoded=True),
        )
        self.message.register(self.handle_command_start, CommandStart(deep_link=False))

    async def handle_command_start_deeplink(
        self, message: Message, command: CommandObject
    ) -> None:
        try:
            deeplink_payload = DeeplinkPayload.model_validate(
                json.loads(command.args or "")
            )
            invited_user_id = str(deeplink_payload.i)
        except ValidationError:
            invited_user_id = None

        await self.handle_command_start(
            message=message, invited_user_id=invited_user_id
        )

    async def handle_command_start(
        self, message: Message, invited_user_id: str | None = None
    ) -> None:
        is_cis = (user := message.from_user) and user.language_code in (
            "ru",
            "ua",
            "kz",
            "by",
        )
        user_telegram_id = message.from_user.id if message.from_user else 0

        asyncio.create_task(
            self.__event_bus_service.emit(
                event=RegisterUserEvent(
                    created_at=get_current_time(),
                    telegram_id=user_telegram_id,
                    invited_user_id=invited_user_id,
                    language=Language.RU if is_cis else Language.EN,
                )
            )
        )
