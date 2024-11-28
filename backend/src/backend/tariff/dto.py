from dataclasses import dataclass

from backend.core.dto import AbstractDTO
from backend.i18n.container import I18nContainer


@dataclass
class TariffDTO(AbstractDTO):
    name: I18nContainer
    price: int
    subscription_duration: int | None
    max_game_accounts: int
