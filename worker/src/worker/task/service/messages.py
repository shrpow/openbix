from dataclasses import dataclass

from worker.emq.service import AbstractMessage


@dataclass(slots=True)
class NewTaskMessage(AbstractMessage):
    game_account_id: str
    auth_data: str
    proxy: str
    captcha_recognition_provider: str
    captcha_recognition_provider_api_key: str


@dataclass
class TaskResultMessage(AbstractMessage):
    game_account_id: str
    was_banned: bool
    balance: int


@dataclass
class InvalidGameAccountMessage(AbstractMessage):
    game_account_id: str


@dataclass
class InternalErrorMessage(AbstractMessage):
    traceback: str
