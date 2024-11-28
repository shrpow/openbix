import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.i18n.language import Language
from backend.telegram.language.events import UpdateUserLanguageEvent
from backend.telegram.language.keyboard import (
    LANGUAGE_SETTINGS_MENU_BUTTON_TEXT,
    get_languages_keyboard,
)
from backend.telegram.middleware import AuthorizationMiddleware
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO


class LanguageSettingsRouter(Router):
    __authorization_middleware: AuthorizationMiddleware
    __event_bus_service: EventBusService

    def __init__(
        self,
        authorization_middleware: AuthorizationMiddleware,
        event_bus_service: EventBusService,
    ) -> None:
        super().__init__()

        self.__authorization_middleware = authorization_middleware
        self.__event_bus_service = event_bus_service

        self.name = "LanguageSettings"

        self.callback_query.middleware.register(self.__authorization_middleware)
        self.message.middleware.register(self.__authorization_middleware)

        self.message.register(
            self.send_language_selector,
            F.text.in_(LANGUAGE_SETTINGS_MENU_BUTTON_TEXT.get_values()),
        )

        self.callback_query.register(
            self.set_language, F.data.startswith("set_language/")
        )

    async def send_language_selector(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        await state.clear()
        await message.answer(
            text=Template.QUESTION_LANGUAGE.render(language=user.language),
            reply_markup=get_languages_keyboard(),
        )

    async def set_language(self, query: CallbackQuery, user: UserDTO) -> None:
        try:
            language = Language((query.data or "").split("/")[-1])
        except ValueError:
            return None

        asyncio.create_task(
            self.__event_bus_service.emit(
                event=UpdateUserLanguageEvent(
                    created_at=get_current_time(), user=user, language=language
                )
            )
        )
