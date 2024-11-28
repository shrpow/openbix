from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from backend.i18n.container import I18nContainer
from backend.i18n.language import Language
from backend.telegram.language.keyboard import LANGUAGE_SETTINGS_MENU_BUTTON_TEXT
from backend.user.core.role import RoleName

MAIN_MENU_BUTTON_TEXT = I18nContainer(ru="🧶 Меню", en="🧶 Menu")


def get_basic_menu_keyboard(language: Language) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MAIN_MENU_BUTTON_TEXT.get_value(language=language)),
                KeyboardButton(
                    text=LANGUAGE_SETTINGS_MENU_BUTTON_TEXT.get_value(language=language)
                ),
            ]
        ],
        resize_keyboard=True,
    )


def get_main_menu_keyboard(role: RoleName, language: Language) -> InlineKeyboardMarkup:
    mbx_accounts_section = [
        InlineKeyboardButton(
            text=I18nContainer(ru="🎮 Аккаунты MBX", en="🎮 MBX Accounts").get_value(
                language=language
            ),
            callback_data="gaccounts/all",
        ),
        InlineKeyboardButton(
            text=I18nContainer(ru="➕ Добавить аккаунт", en="➕ Add Account").get_value(
                language=language
            ),
            callback_data="gaccounts/add",
        ),
    ]

    return {
        RoleName.ADMIN: InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=I18nContainer(
                            ru="🤝 Выдать подписку", en="🤝 Issue a subscription"
                        ).get_value(language=language),
                        callback_data="subscriptions/issue",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=I18nContainer(ru="📈 Статистика", en="📈 Stats").get_value(
                            language=language
                        ),
                        callback_data="stats",
                    ),
                ],
                mbx_accounts_section,
            ]
        ),
        RoleName.CUSTOMER: InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=I18nContainer(
                            ru="👤 Мой профиль", en="👤 My Profile"
                        ).get_value(language=language),
                        callback_data="users/me",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=I18nContainer(
                            ru="💸 Партнёрская программа", en="💸 Partnership"
                        ).get_value(language=language),
                        callback_data="invites/info",
                    ),
                ],
                mbx_accounts_section,
            ]
        ),
    }[role]
