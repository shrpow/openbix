# ruff: noqa: E711
import asyncio

from beanie import SortDirection

from backend.repository.mongo import AbstractMongoMapper, AbstractMongoRepository
from backend.user.dto import UserDTO
from backend.user.models import UserModel


class UserMapper(AbstractMongoMapper[UserDTO, UserModel]):
    def from_model(self, model: UserModel) -> UserDTO:
        return UserDTO(
            uuid=model.uuid,
            created_at=model.created_at,
            deleted_at=model.deleted_at,
            telegram_id=model.telegram_id,
            language=model.language,
            role=model.role,
            balance=model.balance,
        )

    def to_model(self, dto: UserDTO) -> UserModel:
        return UserModel(
            uuid=dto.uuid,
            created_at=dto.created_at,
            deleted_at=dto.deleted_at,
            telegram_id=dto.telegram_id,
            language=dto.language,
            role=dto.role,
            balance=dto.balance,
        )


class UserRepository(AbstractMongoRepository[UserDTO, UserModel]):
    model = UserModel
    mapper: UserMapper = UserMapper()
    __semaphore = asyncio.Semaphore()  # FIXME sorry cringe =(

    async def save(self, data: UserDTO) -> UserDTO:
        async with self.__semaphore:
            return await super().save(data)

    async def is_user_exists(self, telegram_id: int) -> bool:
        return bool(
            await self.model.find_one(
                self.model.telegram_id == telegram_id,
                self.model.deleted_at == None,
            )
        )

    async def find(self, telegram_id: int) -> list[UserDTO]:
        return [
            self.mapper.from_model(model=user)
            async for user in self.model.find(
                self.model.telegram_id == telegram_id, self.model.deleted_at == None
            ).sort((self.model.created_at, SortDirection.DESCENDING))
        ]

    async def get_total_count(self) -> int:
        return await self.model.all().count()
