# ruff: noqa: E711

from beanie import SortDirection

from backend.game_account.core.status import Status
from backend.game_account.dto import GameAccountDTO
from backend.game_account.models import GameAccountModel
from backend.repository.mongo import AbstractMongoMapper, AbstractMongoRepository


class GameAccountMapper(AbstractMongoMapper[GameAccountDTO, GameAccountModel]):
    def from_model(self, model: GameAccountModel) -> GameAccountDTO:
        return GameAccountDTO(
            uuid=model.uuid,
            created_at=model.created_at,
            deleted_at=model.deleted_at,
            user_id=model.user_id,
            status=model.status,
            last_login_at=model.last_login_at,
            balance=model.balance,
            name=model.name,
            auth_data=model.auth_data,
            proxy=model.proxy,
            captcha_recognition_provider=model.captcha_recognition_provider,
            captcha_recognition_provider_api_key=model.captcha_recognition_provider_api_key,
        )

    def to_model(self, dto: GameAccountDTO) -> GameAccountModel:
        return GameAccountModel(
            uuid=dto.uuid,
            created_at=dto.created_at,
            deleted_at=dto.deleted_at,
            user_id=dto.user_id,
            status=dto.status,
            last_login_at=dto.last_login_at,
            balance=dto.balance,
            name=dto.name,
            auth_data=dto.auth_data,
            proxy=dto.proxy,
            captcha_recognition_provider=dto.captcha_recognition_provider,
            captcha_recognition_provider_api_key=dto.captcha_recognition_provider_api_key,
        )


class GameAccountRepository(AbstractMongoRepository[GameAccountDTO, GameAccountModel]):
    model = GameAccountModel
    mapper: GameAccountMapper = GameAccountMapper()

    async def is_exists(self, auth_data: str) -> bool:
        return bool(
            await self.model.find_one(
                self.model.auth_data == auth_data,
                self.model.status == Status.ACTIVE,
                self.model.deleted_at == None,
            )
        )

    async def count_by_user(self, user_id: str, status: Status | None = None) -> int:
        criteria = [self.model.user_id == user_id] + (
            [] if status is None else [self.model.status == status]
        )
        return await self.model.find(*criteria).count()

    async def find(
        self,
        status: Status | None = None,
        user_id: str | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> list[GameAccountDTO]:
        criteria = (
            []
            + ([] if user_id is None else [self.model.user_id == user_id])
            + ([] if status is None else [self.model.status == status])
            + [self.model.deleted_at == None]
        )
        return [
            self.mapper.from_model(model=game_account)
            async for game_account in self.model.find(
                *criteria, skip=offset, limit=limit
            ).sort((self.model.created_at, SortDirection.DESCENDING))
        ]

    async def get_total_count(self) -> int:
        return await self.model.all().count()
