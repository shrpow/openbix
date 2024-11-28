from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from backend.config import Config
from backend.event_bus.service import EventBusService
from backend.i18n.container import I18nContainer
from backend.subscription.dto import SubscriptionDTO
from backend.subscription.service import (
    ActiveSubscriptionNotFoundError,
    SubscriptionService,
)
from backend.telegram.menu.keyboard import (
    MAIN_MENU_BUTTON_TEXT,
    get_basic_menu_keyboard,
    get_main_menu_keyboard,
)
from backend.telegram.middleware import (
    AuthorizationMiddleware,
    SubscriptionRetrieveMiddleware,
)
from backend.telegram.start.events import SendMenuEvent
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO


class MenuRouter(Router):
    __bot: Bot
    __subscription_service: SubscriptionService
    __event_bus_service: EventBusService

    __authz_middleware: AuthorizationMiddleware
    __subscription_retrieve_middleware: SubscriptionRetrieveMiddleware

    def __init__(
        self,
        bot: Bot,
        subscription_service: SubscriptionService,
        event_bus_service: EventBusService,
        authorization_middleware: AuthorizationMiddleware,
        subscription_retrieve_middleware: SubscriptionRetrieveMiddleware,
    ) -> None:
        super().__init__()

        self.__bot = bot
        self.__event_bus_service = event_bus_service
        self.__subscription_service = subscription_service
        self.__authz_middleware = authorization_middleware
        self.__subscription_retrieve_middleware = subscription_retrieve_middleware

        self.name = "Menu"

        self.__event_bus_service.on_event(
            event_type=SendMenuEvent, callback=self.on_menu_event
        )

        self.message.middleware.register(middleware=self.__authz_middleware)
        self.message.middleware.register(
            middleware=self.__subscription_retrieve_middleware
        )
        self.message.register(
            self.send_menu, F.text.in_(MAIN_MENU_BUTTON_TEXT.get_values())
        )

    async def on_menu_event(self, event: SendMenuEvent) -> None:
        try:
            subscription = await self.__subscription_service.get(
                user=event.user, user_id=event.user.uuid
            )
        except ActiveSubscriptionNotFoundError:
            subscription = None

        await self.send_menu(
            user=event.user, subscription=subscription, state=None, message=None
        )

    async def send_menu(
        self,
        message: Message | None,
        user: UserDTO,
        subscription: SubscriptionDTO | None,
        state: FSMContext | None,
    ) -> None:
        if state is not None:
            await state.clear()

        message = await self.__bot.send_message(
            chat_id=user.telegram_id,
            text=Template.NOTIFICATION_GREETING.render(language=user.language),
            reply_markup=get_basic_menu_keyboard(language=user.language),
        )

        if subscription is None:
            await message.answer(
                text=Template.NOTIFICATION_NO_SUBSCRIPTION.render(
                    language=user.language, support=f"@{Config.TG_SUPPORT_USERNAME}"
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=I18nContainer(
                                    ru="👾 Доступные тарифы", en="👾 Available tariffs"
                                ).get_value(language=user.language),
                                callback_data="tariffs/all",
                            )
                        ]
                    ]
                ),
            )
            return None

        await message.answer(
            text=Template.INFO_MAIN_MENU.render(language=user.language),
            reply_markup=get_main_menu_keyboard(role=user.role, language=user.language),
        )
