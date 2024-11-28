from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from backend.config import Config
from backend.tariff.service import TariffService
from backend.telegram.middleware import AuthorizationMiddleware
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO


class TariffRouter(Router):
    __tariff_service: TariffService
    __authorization_middleware: AuthorizationMiddleware

    def __init__(
        self,
        tariff_service: TariffService,
        authorization_middleware: AuthorizationMiddleware,
    ) -> None:
        super().__init__()

        self.name = "Tariff"

        self.__tariff_service = tariff_service
        self.__authorization_middleware = authorization_middleware

        self.callback_query.middleware.register(self.__authorization_middleware)
        self.callback_query.register(self.send_tariffs_info, F.data == "tariffs/all")

    async def send_tariffs_info(self, query: CallbackQuery, user: UserDTO) -> None:
        await query.message.answer(  # type: ignore
            text=Template.INFO_TARIFFS.render(language=user.language),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=Template.INFO_TARIFF_ITEM.render(
                                language=user.language, tariff=tariff
                            ),
                            url=f"https://t.me/{Config.TG_SUPPORT_USERNAME}",
                        )
                    ]
                    for tariff in await self.__tariff_service.get_all()
                ]
            ),
        )
