from dataclasses import dataclass

from backend.core.entity import AbstractEntity
from backend.core.utils import generate_uuid, get_current_time
from backend.i18n.container import I18nContainer


class InvalidTariffDataError(Exception):
    ...


@dataclass
class Tariff(AbstractEntity):
    name: I18nContainer
    price: int
    subscription_duration: int | None
    max_game_accounts: int

    @staticmethod
    def create(
        name: I18nContainer,
        price: int,
        subscription_duration: int | None,
        max_game_accounts: int,
        uuid: str | None = None,
    ) -> "Tariff":
        if not price >= 0:
            raise InvalidTariffDataError(f"{price=}")

        if subscription_duration is not None and not subscription_duration >= 3:
            raise InvalidTariffDataError(f"{subscription_duration=}")

        if not 0 < max_game_accounts <= 500:
            raise InvalidTariffDataError(f"{max_game_accounts=}")

        return Tariff(
            uuid=uuid or generate_uuid(),
            created_at=get_current_time(),
            deleted_at=None,
            name=name,
            price=price,
            subscription_duration=subscription_duration,
            max_game_accounts=max_game_accounts,
        )

    def update(
        self,
        name: str | None = None,
        price: int | None = None,
        subscription_duration: int | None = None,
        max_game_accounts: int | None = None,
    ) -> "Tariff":
        raise NotImplementedError
