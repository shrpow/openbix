from aiogram import Bot, F, Router
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from backend.event_bus.service import EventBusService
from backend.i18n.container import I18nContainer
from backend.subscription.events import SubscriptionCreatedEvent
from backend.subscription.service import (
    ActiveSubscriptionNotFoundError,
    SubscriptionService,
)
from backend.tariff.dto import TariffDTO
from backend.tariff.repository import TariffNotFoundError
from backend.tariff.service import TariffService
from backend.telegram.middleware import AuthorizationMiddleware
from backend.telegram.subscription.states import IssueQueryField, SubscriptionIssueState
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO
from backend.user.service import UserNotExistsError, UserService


class SubscriptionRouter(Router):
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

        self.name = "Subscription"

        self.__event_bus_service.on_event(
            event_type=SubscriptionCreatedEvent, callback=self.on_subscription_create
        )

        self.callback_query.middleware.register(self.__authorization_middleware)
        self.message.middleware.register(self.__authorization_middleware)

        self.message.register(
            self.handle_user_telegram_id_question_answer,
            StateFilter(SubscriptionIssueState.waiting_for_telegram_id),
        )
        self.callback_query.register(
            self.handle_tariff_button_press,
            F.data.startswith("subscriptions/tariff/"),
            StateFilter(SubscriptionIssueState.waiting_for_tariff),
        )
        self.callback_query.register(
            self.handle_create_button_press,
            F.data.startswith("subscriptions/issue/"),
            StateFilter(SubscriptionIssueState.waiting_for_tariff),
        )

        self.callback_query.register(
            self.send_user_telegram_id_question, F.data == "subscriptions/issue"
        )

    async def on_subscription_create(self, event: SubscriptionCreatedEvent) -> None:
        customer = await self.__user_service.get_by_id(
            user=event.issuer, uuid=event.subscription.user_id
        )
        await self.__bot.send_message(
            chat_id=event.issuer.telegram_id,
            text=Template.NOTIFICATION_SUBSCRIPTION_ISSUED.render(
                language=event.issuer.language
            ),
        )
        await self.__bot.send_message(
            chat_id=customer.telegram_id,
            text=Template.NOTIFICATION_SUBSCRIPTION_PURCHASED.render(
                language=customer.language,
                tariff=event.tariff,
                subscription=event.subscription,
            ),
        )

    async def send_user_telegram_id_question(
        self, query: CallbackQuery, user: UserDTO, state: FSMContext
    ) -> None:
        await state.set_state(state=SubscriptionIssueState.waiting_for_telegram_id)
        await query.message.answer(  # type: ignore
            text=Template.QUESTION_USER_TELEGRAM_ID.render(language=user.language)
        )

    async def handle_user_telegram_id_question_answer(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        if not (telegram_id := message.text or "").isdigit():
            await message.answer(
                text=Template.NOTIFICATION_INVALID_TELEGRAM_ID.render(
                    language=user.language
                )
            )
            return None

        try:
            found_user = await self.__user_service.find_by_telegram_id(
                telegram_id=int(telegram_id)
            )
        except UserNotExistsError:
            await message.answer(
                text=Template.NOTIFICATION_USER_NOT_FOUND.render(language=user.language)
            )
            return None

        try:
            await self.__subscription_service.get(user=user, user_id=found_user.uuid)
            await message.answer(
                text=Template.NOTIFICATION_USER_ALREADY_HAS_SUBSCRIPTION.render(
                    language=user.language
                )
            )
        except ActiveSubscriptionNotFoundError:
            ...

        await state.update_data({IssueQueryField.TARGET_USER: found_user})
        await self.send_tariff_question(message=message, user=user, state=state)

    async def send_tariff_question(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        await state.set_state(state=SubscriptionIssueState.waiting_for_tariff)
        await message.answer(
            text=Template.QUESTION_TARIFF.render(language=user.language),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=Template.INFO_TARIFF_ITEM.render(
                                language=user.language, tariff=tariff
                            ),
                            callback_data=f"subscriptions/tariff/{tariff.uuid}",
                        )
                    ]
                    for tariff in await self.__tariff_service.get_all()
                ]
            ),
        )

    async def handle_tariff_button_press(
        self, query: CallbackQuery, user: UserDTO, state: FSMContext
    ) -> None:
        if (message := query.message) is None:
            return None

        tariff_id = (query.data or "").split("/")[-1]

        try:
            selected_tariff = await self.__tariff_service.get(uuid=tariff_id)
        except TariffNotFoundError:
            await query.answer("TariffNotFoundError")
            return None

        await state.update_data({IssueQueryField.TARIFF: selected_tariff})

        await self.send_subscription_preview(message=message, user=user, state=state)  # type: ignore

    async def send_subscription_preview(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        state_data = await state.get_data()
        target_user: UserDTO = state_data[IssueQueryField.TARGET_USER]
        tariff: TariffDTO = state_data[IssueQueryField.TARIFF]
        subscription_preview = await self.__subscription_service.create_preview(
            user=user,
            user_id=target_user.uuid,
            tariff_id=tariff.uuid,
            duration=tariff.subscription_duration,
        )

        await message.answer(
            text=Template.INFO_SUBSCRIPTION_PREVIEW.render(
                language=user.language,
                user=target_user,
                tariff=tariff,
                subscription=subscription_preview,
                discount_price=str(max(0, tariff.price - user.balance))
                if target_user.balance
                else "-",
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=I18nContainer(ru="Выдать", en="Issue").get_value(
                                language=user.language
                            ),
                            callback_data="subscriptions/issue/",
                        )
                    ],
                ]
                + (
                    [
                        [
                            InlineKeyboardButton(
                                text=I18nContainer(
                                    ru="Выдать и вывести", en="Issue and withdraw"
                                ).get_value(language=user.language),
                                callback_data="subscriptions/issue/withdraw",
                            )
                        ]
                    ]
                    if target_user.balance
                    else []
                )
            ),
        )

    async def handle_create_button_press(
        self, query: CallbackQuery, user: UserDTO, state: FSMContext
    ) -> None:
        is_withdraw_needed = (query.data or "").split("/")[-1] == "withdraw"

        state_data = await state.get_data()
        target_user: UserDTO = state_data[IssueQueryField.TARGET_USER]
        tariff: TariffDTO = state_data[IssueQueryField.TARIFF]

        await self.__subscription_service.create(
            user=user,
            user_id=target_user.uuid,
            tariff_id=tariff.uuid,
            duration=tariff.subscription_duration,
            is_withdraw_needed=is_withdraw_needed,
        )

        await state.clear()
