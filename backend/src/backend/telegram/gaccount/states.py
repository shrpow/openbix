import enum

from aiogram.fsm.state import State, StatesGroup


class GameAccountCreatorState(StatesGroup):
    waiting_for_name = State()
    waiting_for_webapp_url = State()
    waiting_for_proxy = State()
    waiting_for_captcha_recognition_provider_api_key = State()


class AccountField(enum.StrEnum):
    NAME = enum.auto()
    WEBAPP_URL = enum.auto()
    PROXY = enum.auto()
    CAPTCHA_RECOGNITION_PROVIDER_API_KEY = enum.auto()
