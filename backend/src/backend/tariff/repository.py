from backend.i18n.container import I18nContainer
from backend.repository.base import IMapper, IRepository
from backend.tariff.core.tariff import Tariff
from backend.tariff.dto import TariffDTO


class TariffNotFoundError(Exception):
    ...


class TariffMapper(IMapper[TariffDTO, Tariff]):
    def from_model(self, model: Tariff) -> TariffDTO:
        return TariffDTO(
            uuid=model.uuid,
            created_at=model.created_at,
            deleted_at=model.deleted_at,
            name=model.name,
            price=model.price,
            subscription_duration=model.subscription_duration,
            max_game_accounts=model.max_game_accounts,
        )

    def to_model(self, dto: TariffDTO) -> Tariff:
        return Tariff(
            uuid=dto.uuid,
            created_at=dto.created_at,
            deleted_at=dto.deleted_at,
            name=dto.name,
            price=dto.price,
            subscription_duration=dto.subscription_duration,
            max_game_accounts=dto.max_game_accounts,
        )


class TariffRepository(IRepository[TariffDTO]):
    TARIFFS: dict[str, Tariff] = {
        "v1-trial": Tariff.create(
            name=I18nContainer(ru="⚡️ Пробный", en="⚡️ Trial"),
            price=0,
            subscription_duration=3,
            max_game_accounts=1,
            uuid="v1-trial",
        ),
        "v1-weekly": Tariff.create(
            name=I18nContainer(ru="🎟️ Недельный", en="🎟️ Weekly"),
            price=10,
            subscription_duration=7 * 24,
            max_game_accounts=10,
            uuid="v1-weekly",
        ),
        "v1-weekly-extended": Tariff.create(
            name=I18nContainer(ru="🎟️ Недельный +", en="🎟️ Weekly +"),
            price=19,
            subscription_duration=7 * 24,
            max_game_accounts=50,
            uuid="v1-weekly-extended",
        ),
        "v1-monthly": Tariff.create(
            name=I18nContainer(ru="🌀 Месячный", en="🌀 Monthly"),
            price=30,
            subscription_duration=30 * 24,
            max_game_accounts=10,
            uuid="v1-monthly",
        ),
        "v1-monthly-extended": Tariff.create(
            name=I18nContainer(ru="🌀 Месячный +", en="🌀 Monthly +"),
            price=59,
            subscription_duration=30 * 24,
            max_game_accounts=50,
            uuid="v1-monthly-extended",
        ),
        "v1-lifetime": Tariff.create(
            name=I18nContainer(ru="🏝️ Навсегда", en="🏝️ Lifetime"),
            price=228,
            subscription_duration=None,
            max_game_accounts=100,
            uuid="v1-lifetime",
        ),
    }
    mapper: TariffMapper = TariffMapper()

    async def get(self, uuid: str) -> TariffDTO:
        if tariff := self.TARIFFS.get(uuid):
            return self.mapper.from_model(model=tariff)

        raise TariffNotFoundError(uuid)

    async def get_all(self, offset: int, limit: int) -> list[TariffDTO]:
        return [
            self.mapper.from_model(model=model)
            for model in list(self.TARIFFS.values())[offset:limit]
        ]

    async def save(self, data: TariffDTO) -> TariffDTO:
        raise NotImplementedError

    async def delete(self, uuid: str) -> TariffDTO:
        raise NotImplementedError
