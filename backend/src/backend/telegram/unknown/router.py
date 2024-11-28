import asyncio

from aiogram import Router
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery, Message
from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.telegram.middleware import (
    AuthorizationMiddleware,
    CallbackQueryAnswerMiddleware,
)
from backend.telegram.start.events import SendMenuEvent
from backend.user.dto import UserDTO


class UnknownCommandRouter(Router):
    __event_bus_service: EventBusService
    __authorization_middleware: AuthorizationMiddleware
    __callback_query_answer_middleware: CallbackQueryAnswerMiddleware

    def __init__(
        self,
        event_bus_service: EventBusService,
        authorization_middleware: AuthorizationMiddleware,
        callback_query_answer_middleware: CallbackQueryAnswerMiddleware,
    ) -> None:
        super().__init__()

        self.name = "UnknownCommand"

        self.__event_bus_service = event_bus_service
        self.__authorization_middleware = authorization_middleware
        self.__callback_query_answer_middleware = callback_query_answer_middleware

        self.callback_query.middleware.register(self.__callback_query_answer_middleware)
        self.callback_query.register(self.skip_unknown_query)

        self.message.middleware.register(self.__authorization_middleware)
        self.message.register(self.send_menu_on_unknown_command, StateFilter(None))

    async def skip_unknown_query(self, query: CallbackQuery) -> None:
        await query.answer()

    async def send_menu_on_unknown_command(
        self, message: Message, user: UserDTO
    ) -> None:
        asyncio.create_task(
            self.__event_bus_service.emit(
                event=SendMenuEvent(created_at=get_current_time(), user=user)
            )
        )
