import asyncio

from aiogram import Bot, F, Router
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from backend.core.utils import get_current_time
from backend.game_account.core.auth_data import InvalidAuthDataError
from backend.game_account.core.proxy import InvalidProxyError
from backend.game_account.service import (
    GameAccountAlreadyExistsError,
    GameAccountCannotBeCreatedError,
    GameAccountService,
)
from backend.telegram.gaccount.states import AccountField, GameAccountCreatorState
from backend.telegram.middleware import (
    AuthorizationMiddleware,
    ParticipiationCheckMiddleware,
)
from backend.telegram.template.template import Template
from backend.user.dto import UserDTO


class GameAccountRouter(Router):
    __game_account_service: GameAccountService
    __authorization_middleware: AuthorizationMiddleware
    __participiation_check_middleware: ParticipiationCheckMiddleware

    def __init__(
        self,
        game_account_service: GameAccountService,
        authorization_middleware: AuthorizationMiddleware,
        participiation_check_middleware: ParticipiationCheckMiddleware,
    ) -> None:
        super().__init__()

        self.__game_account_service = game_account_service
        self.__authorization_middleware = authorization_middleware
        self.__participiation_check_middleware = participiation_check_middleware

        self.name = "GameAccount"

        self.callback_query.middleware.register(self.__authorization_middleware)
        self.callback_query.middleware.register(self.__participiation_check_middleware)

        self.message.middleware.register(self.__authorization_middleware)
        self.message.middleware.register(self.__participiation_check_middleware)

        self.callback_query.register(
            self.send_account_list, F.data.startswith("gaccounts/all")
        )
        self.callback_query.register(
            self.handle_add_account_button_press, F.data == "gaccounts/add"
        )

        self.message.register(
            self.handle_name_question_answer,
            StateFilter(GameAccountCreatorState.waiting_for_name),
        )
        self.message.register(
            self.handle_webapp_url_question_answer,
            StateFilter(GameAccountCreatorState.waiting_for_webapp_url),
        )
        self.message.register(
            self.handle_captcha_recognition_provider_api_key_question_answer,
            StateFilter(
                GameAccountCreatorState.waiting_for_captcha_recognition_provider_api_key
            ),
        )
        self.message.register(
            self.handle_proxy_question_answer,
            StateFilter(GameAccountCreatorState.waiting_for_proxy),
        )

    async def handle_add_account_button_press(
        self, query: CallbackQuery, user: UserDTO, state: FSMContext
    ) -> None:
        message: Message = query.message  # type: ignore

        if not await self.__game_account_service.is_possible_to_create(
            user=user, user_id=user.uuid
        ):
            await message.answer(
                text=Template.NOTIFICATION_GAME_ACCOUNT_CANNOT_BE_CREATED.render(
                    language=user.language
                )
            )
            return None

        await self.send_name_question(message=message, user=user, state=state)

    async def send_name_question(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        await state.set_state(GameAccountCreatorState.waiting_for_name)
        await message.answer(
            text=Template.QUESTION_GAME_ACCOUNT_NAME.render(language=user.language)
        )

    async def handle_name_question_answer(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        message_text = message.text or ""

        if not 1 <= len(message_text) <= 30:
            await message.answer(
                text=Template.NOTIFICATION_INVALID_GAME_ACCOUNT_NAME.render(
                    language=user.language
                )
            )
            return None

        await state.update_data({AccountField.NAME: message_text})
        await self.send_webapp_url_question(message=message, user=user, state=state)

    async def send_webapp_url_question(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        await state.set_state(GameAccountCreatorState.waiting_for_webapp_url)
        await message.answer(
            text=Template.QUESTION_GAME_ACCOUNT_WEB_APP_LINK.render(
                language=user.language
            )
        )

    async def handle_webapp_url_question_answer(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        message_text = message.text or ""

        if (
            "/game/tg/moon-bix" not in message_text
            or not 100 <= len(message_text) <= 2000
        ):
            await message.answer(
                text=Template.NOTIFICATION_INVALID_WEB_APP_LINK.render(
                    language=user.language
                )
            )
            return None

        await state.update_data({AccountField.WEBAPP_URL: message_text})
        await self.send_proxy_question(message=message, user=user, state=state)

    async def send_proxy_question(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        await state.set_state(GameAccountCreatorState.waiting_for_proxy)
        await message.answer(
            text=Template.QUESTION_GAME_ACCOUNT_PROXY.render(language=user.language)
        )

    async def handle_proxy_question_answer(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        message_text = message.text or ""

        if (
            not any([protocol in message_text for protocol in ("http", "socks")])
            or not 15 <= len(message_text) <= 300
        ):
            await message.answer(
                text=Template.NOTIFICATION_INVALID_PROXY.render(language=user.language)
            )
            return None

        await state.update_data({AccountField.PROXY: message_text})
        await self.send_captcha_recognition_provider_api_key_question(
            message=message, user=user, state=state
        )

    async def send_captcha_recognition_provider_api_key_question(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        await state.set_state(
            GameAccountCreatorState.waiting_for_captcha_recognition_provider_api_key
        )
        await message.answer(
            text=Template.QUESTION_CAPTCHA_RECOGNITION_PROVIDER_API_KEY.render(
                language=user.language
            )
        )

    async def handle_captcha_recognition_provider_api_key_question_answer(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        message_text = message.text or ""

        if not len(message_text) == 32:
            await message.answer(
                text=Template.NOTIFICATION_INVALID_CAPTCHA_RECOGNITION_PROVIDER_API_KEY.render(
                    language=user.language
                )
            )
            return None

        await state.update_data(
            {AccountField.CAPTCHA_RECOGNITION_PROVIDER_API_KEY: message_text}
        )
        await self.create_game_account(message=message, user=user, state=state)

    async def create_game_account(
        self, message: Message, user: UserDTO, state: FSMContext
    ) -> None:
        state_data = await state.get_data()

        try:
            await self.__game_account_service.create(
                user=user,
                user_id=user.uuid,
                name=state_data[AccountField.NAME],
                full_url=state_data[AccountField.WEBAPP_URL],
                proxy=state_data[AccountField.PROXY],
                captcha_recognition_provider_api_key=state_data[
                    AccountField.CAPTCHA_RECOGNITION_PROVIDER_API_KEY
                ],
            )
        except (
            InvalidProxyError,
            InvalidAuthDataError,
            GameAccountAlreadyExistsError,
            GameAccountCannotBeCreatedError,
        ) as exc:
            await message.answer(
                text=Template.NOTIFICATION_INVALID_SOMETHING.render(
                    language=user.language
                )
            )
            return None

        await state.clear()
        await message.answer(
            text=Template.NOTIFICATION_GAME_ACCOUNT_CREATED.render(
                language=user.language
            )
        )

    async def send_account_list(self, query: CallbackQuery, user: UserDTO) -> None:
        offset_data = (query.data or "").split("/")[-1]
        offset = (
            int(offset_data) if (is_offset_specified := (offset_data).isdigit()) else 0
        )

        if is_offset_specified:
            message: Message = query.message  # type: ignore
        else:
            message = await query.message.answer(  # type: ignore
                text=Template.INFO_GAME_ACCOUNT.render_skeleton(language=user.language)
            )

        game_accounts, game_accounts_count = await asyncio.gather(
            self.__game_account_service.get_all(
                user=user, user_id=user.uuid, offset=offset, limit=1
            ),
            self.__game_account_service.get_count(user=user, user_id=user.uuid),
        )

        if not game_accounts:
            await message.edit_text(
                text=Template.NOTIFICATION_NO_GAME_ACCOUNTS_ADDED.render(
                    language=user.language
                )
            )
            return None

        game_account = game_accounts[0]

        await message.edit_text(
            text=Template.INFO_GAME_ACCOUNT.render(
                language=user.language,
                offset=offset + 1,
                total_count=game_accounts_count,
                game_account=game_account,
                current_time=get_current_time(),
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⏮️",
                            callback_data="gaccounts/all/0" if offset > 0 else "empty",
                        ),
                        InlineKeyboardButton(
                            text="⬅️",
                            callback_data=f"gaccounts/all/{max(0, offset - 1)}"
                            if offset > 0
                            else "empty",
                        ),
                        InlineKeyboardButton(
                            text="➡️",
                            callback_data=f"gaccounts/all/{offset + 1}"
                            if offset + 1 < game_accounts_count
                            else "empty",
                        ),
                        InlineKeyboardButton(
                            text="⏭️",
                            callback_data=f"gaccounts/all/{game_accounts_count-1}"
                            if offset + 1 < game_accounts_count
                            else "empty",
                        ),
                    ],
                ]
            ),
        )
