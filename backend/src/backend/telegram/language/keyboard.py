from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from backend.i18n.container import I18nContainer
from backend.i18n.language import Language

LANGUAGE_SETTINGS_MENU_BUTTON_TEXT = I18nContainer(
    ru="🌍 Сменить язык", en="🌍 Set language"
)


def get_languages_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский", callback_data=f"set_language/{Language.RU}"
                ),
                InlineKeyboardButton(
                    text="🇺🇸 English", callback_data=f"set_language/{Language.EN}"
                ),
            ]
        ]
    )
