# ruff: noqa: E711
from datetime import datetime

from beanie import SortDirection
from beanie.operators import Or

from backend.repository.mongo import AbstractMongoMapper, AbstractMongoRepository
from backend.subscription.dto import SubscriptionDTO
from backend.subscription.models import SubscriptionModel


class SubscriptionMapper(AbstractMongoMapper[SubscriptionDTO, SubscriptionModel]):
    def from_model(self, model: SubscriptionModel) -> SubscriptionDTO:
        return SubscriptionDTO(
            uuid=model.uuid,
            created_at=model.created_at,
            deleted_at=model.deleted_at,
            tariff_id=model.tariff_id,
            user_id=model.user_id,
            paid=model.paid,
            active_from=model.active_from,
            active_until=model.active_until,
        )

    def to_model(self, dto: SubscriptionDTO) -> SubscriptionModel:
        return SubscriptionModel(
            uuid=dto.uuid,
            created_at=dto.created_at,
            deleted_at=dto.deleted_at,
            tariff_id=dto.tariff_id,
            user_id=dto.user_id,
            paid=dto.paid,
            active_from=dto.active_from,
            active_until=dto.active_until,
        )


class SubscriptionRepository(
    AbstractMongoRepository[SubscriptionDTO, SubscriptionModel]
):
    model = SubscriptionModel
    mapper: SubscriptionMapper = SubscriptionMapper()

    async def find(
        self, user_id: str, active_until: datetime, offset: int = 0, limit: int = 25
    ) -> list[SubscriptionDTO]:
        return [
            self.mapper.from_model(model=subscription)
            async for subscription in self.model.find(
                self.model.user_id == user_id,
                Or(
                    self.model.active_until == None,  # type: ignore
                    self.model.active_until >= active_until,  # type: ignore
                ),
                self.model.deleted_at == None,
                skip=offset,
                limit=limit,
            ).sort((self.model.created_at, SortDirection.DESCENDING))
        ]
