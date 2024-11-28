from dataclasses import dataclass

from backend.core.message import AbstractMessage


@dataclass
class InvalidGameAccountMessage(AbstractMessage):
    game_account_id: str
