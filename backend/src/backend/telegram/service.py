from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from backend.config import Config
from backend.event_bus.service import EventBusService
from backend.game_account.service import GameAccountService
from backend.invite.service import InviteService
from backend.subscription.service import SubscriptionService
from backend.tariff.service import TariffService
from backend.telegram.gaccount.router import GameAccountRouter
from backend.telegram.invite.router import InviteStatsRouter
from backend.telegram.language.router import LanguageSettingsRouter
from backend.telegram.menu.router import MenuRouter
from backend.telegram.middleware import (
    AuthorizationMiddleware,
    CallbackQueryAnswerMiddleware,
    InteractionMiddleware,
    ParticipiationCheckMiddleware,
    SubscriptionRetrieveMiddleware,
)
from backend.telegram.start.router import StartRouter
from backend.telegram.subscription.router import SubscriptionRouter
from backend.telegram.tariff.router import TariffRouter
from backend.telegram.unknown.router import UnknownCommandRouter
from backend.telegram.user.router import UserRouter
from backend.user.service import UserService


class TelegramService:
    __user_service: UserService
    __tariff_service: TariffService
    __subscription_service: SubscriptionService
    __invite_service: InviteService
    __game_account_service: GameAccountService
    __event_bus_service: EventBusService

    def __init__(
        self,
        user_service: UserService,
        tariff_service: TariffService,
        subscription_service: SubscriptionService,
        invite_service: InviteService,
        game_account_service: GameAccountService,
        event_bus_service: EventBusService,
    ) -> None:
        self.__user_service = user_service
        self.__tariff_service = tariff_service
        self.__subscription_service = subscription_service
        self.__invite_service = invite_service
        self.__game_account_service = game_account_service
        self.__event_bus_service = event_bus_service

    async def start(self) -> None:
        bot = Bot(
            token=Config.TG_BOT_TOKEN, default=DefaultBotProperties(parse_mode="html")
        )
        dp = Dispatcher()

        interaction_middleware = InteractionMiddleware(
            event_bus_service=self.__event_bus_service
        )
        participiation_check_middleware = ParticipiationCheckMiddleware()
        authorization_middleware = AuthorizationMiddleware(
            user_service=self.__user_service
        )
        subscription_retrieve_middleware = SubscriptionRetrieveMiddleware(
            subscription_service=self.__subscription_service
        )
        callback_query_answer_middleware = CallbackQueryAnswerMiddleware()

        dp.callback_query.middleware.register(interaction_middleware)
        dp.message.middleware.register(interaction_middleware)

        dp.include_routers(
            StartRouter(event_bus_service=self.__event_bus_service),
            MenuRouter(
                bot=bot,
                authorization_middleware=authorization_middleware,
                subscription_retrieve_middleware=subscription_retrieve_middleware,
                subscription_service=self.__subscription_service,
                event_bus_service=self.__event_bus_service,
            ),
            TariffRouter(
                tariff_service=self.__tariff_service,
                authorization_middleware=authorization_middleware,
            ),
            LanguageSettingsRouter(
                authorization_middleware=authorization_middleware,
                event_bus_service=self.__event_bus_service,
            ),
            UserRouter(
                bot=bot,
                event_bus_service=self.__event_bus_service,
                authorization_middleware=authorization_middleware,
                user_service=self.__user_service,
                tariff_service=self.__tariff_service,
                subscription_service=self.__subscription_service,
            ),
            InviteStatsRouter(
                bot=bot,
                invite_service=self.__invite_service,
                authorization_middleware=authorization_middleware,
            ),
            SubscriptionRouter(
                bot=bot,
                event_bus_service=self.__event_bus_service,
                authorization_middleware=authorization_middleware,
                user_service=self.__user_service,
                tariff_service=self.__tariff_service,
                subscription_service=self.__subscription_service,
            ),
            GameAccountRouter(
                game_account_service=self.__game_account_service,
                authorization_middleware=authorization_middleware,
                participiation_check_middleware=participiation_check_middleware,
            ),
            UnknownCommandRouter(
                event_bus_service=self.__event_bus_service,
                authorization_middleware=authorization_middleware,
                callback_query_answer_middleware=callback_query_answer_middleware,
            ),
        )

        await dp.start_polling(bot)
