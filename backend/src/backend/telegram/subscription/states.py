import enum

from aiogram.fsm.state import State, StatesGroup


class SubscriptionIssueState(StatesGroup):
    waiting_for_telegram_id = State()
    waiting_for_tariff = State()


class IssueQueryField(enum.StrEnum):
    TARGET_USER = enum.auto()
    TARIFF = enum.auto()
