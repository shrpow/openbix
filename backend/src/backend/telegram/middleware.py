import asyncio
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot
from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.types import CallbackQuery, TelegramObject
from backend.config import Config
from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.subscription.service import (
    ActiveSubscriptionNotFoundError,
    SubscriptionService,
)
from backend.telegram.events import UserInteractedWithBotEvent
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO
from backend.user.service import UserNotExistsError, UserService


class InteractionMiddleware(BaseMiddleware):
    __event_bus_service: EventBusService

    def __init__(self, event_bus_service: EventBusService) -> None:
        super().__init__()
        self.__event_bus_service = event_bus_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        asyncio.create_task(
            self.__event_bus_service.emit(
                event=UserInteractedWithBotEvent(created_at=get_current_time())
            )
        )
        return await handler(event, data)


class AuthorizationMiddleware(BaseMiddleware):
    __user_service: UserService

    def __init__(self, user_service: UserService) -> None:
        super().__init__()
        self.__user_service = user_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user_telegram_id = data["event_from_user"].id

        try:
            user = await self.__user_service.find_by_telegram_id(
                telegram_id=user_telegram_id
            )
        except UserNotExistsError:
            return None

        result = await handler(event, data | {"user": user})

        if isinstance(event, CallbackQuery):
            await event.answer()

        return result


class SubscriptionRetrieveMiddleware(BaseMiddleware):
    __subscription_service: SubscriptionService

    def __init__(self, subscription_service: SubscriptionService) -> None:
        super().__init__()
        self.__subscription_service = subscription_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: UserDTO = data["user"]

        try:
            subscription = await self.__subscription_service.get(
                user=user, user_id=user.uuid
            )
        except ActiveSubscriptionNotFoundError:
            subscription = None

        result = await handler(event, data | {"subscription": subscription})

        if isinstance(event, CallbackQuery):
            await event.answer()

        return result


class ParticipiationCheckMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]
        user: UserDTO = data["user"]

        chat_member = await bot.get_chat_member(
            chat_id=Config.TG_NEWS_CHANNEL_NAME, user_id=user.telegram_id
        )

        if chat_member.status not in (
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER,
        ):
            await bot.send_message(
                chat_id=user.telegram_id,
                text=Template.NOTIFICATION_PARTICIPIATION_NEEDED.render(
                    language=user.language, channel_name=Config.TG_NEWS_CHANNEL_NAME
                ),
            )
            return None

        result = await handler(event, data)
        return result


class CallbackQueryAnswerMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery):
            await event.answer()
        return await handler(event, data)
