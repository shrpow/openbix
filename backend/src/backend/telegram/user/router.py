import asyncio

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.subscription.service import (
    ActiveSubscriptionNotFoundError,
    SubscriptionService,
)
from backend.tariff.service import TariffService
from backend.telegram.language.events import UpdateUserLanguageEvent
from backend.telegram.middleware import AuthorizationMiddleware
from backend.telegram.start.events import RegisterUserEvent, SendMenuEvent
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO
from backend.user.service import UserAlreadyExistsError, UserService
from loguru import logger


class UserRouter(Router):
    __bot: Bot
    __event_bus_service: EventBusService
    __authorization_middleware: AuthorizationMiddleware
    __user_service: UserService
    __tariff_service: TariffService
    __subscription_service: SubscriptionService

    def __init__(
        self,
        bot: Bot,
        event_bus_service: EventBusService,
        authorization_middleware: AuthorizationMiddleware,
        user_service: UserService,
        tariff_service: TariffService,
        subscription_service: SubscriptionService,
    ) -> None:
        super().__init__()

        self.__bot = bot
        self.__event_bus_service = event_bus_service
        self.__authorization_middleware = authorization_middleware
        self.__user_service = user_service
        self.__tariff_service = tariff_service
        self.__subscription_service = subscription_service

        self.name = "User"

        self.callback_query.middleware.register(self.__authorization_middleware)
        self.message.middleware.register(self.__authorization_middleware)

        self.callback_query.register(
            self.handle_profile_info_button_press, F.data == "users/me"
        )

        self.__event_bus_service.on_event(
            event_type=UpdateUserLanguageEvent, callback=self.on_user_language_update
        )
        self.__event_bus_service.on_event(
            event_type=RegisterUserEvent, callback=self.on_user_register
        )

    async def handle_profile_info_button_press(
        self, query: CallbackQuery, user: UserDTO
    ) -> None:
        try:
            subscription = await self.__subscription_service.get(
                user=user, user_id=user.uuid
            )
        except ActiveSubscriptionNotFoundError:
            subscription = None

        tariff = (
            None
            if subscription is None
            else await self.__tariff_service.get(uuid=subscription.tariff_id)
        )

        await query.message.answer(  # type: ignore
            text=Template.INFO_USER_PROFILE.render(
                language=user.language,
                user=user,
                tariff=tariff,
                subscription=subscription,
            )
        )

    async def on_user_language_update(self, event: UpdateUserLanguageEvent) -> None:
        updated_user = await self.__user_service.update(
            user=event.user, user_id=event.user.uuid, language=event.language
        )
        await self.__bot.send_message(
            chat_id=event.user.telegram_id,
            text=Template.NOTIFICATION_LANGUAGE_SET.render(
                language=updated_user.language
            ),
        )

    async def on_user_register(self, event: RegisterUserEvent) -> None:
        try:
            user = await self.__user_service.create(
                telegram_id=event.telegram_id,
                language=event.language,
                invited_user_id=event.invited_user_id,
            )
            logger.success(f"{user=} has just registered!")
        except UserAlreadyExistsError:  # FIXME нахуй нам второй запрос тут
            user = await self.__user_service.find_by_telegram_id(
                telegram_id=event.telegram_id
            )

        asyncio.create_task(
            self.__event_bus_service.emit(
                event=SendMenuEvent(created_at=get_current_time(), user=user)
            )
        )
