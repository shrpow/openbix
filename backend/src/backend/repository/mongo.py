# ruff: noqa: E711
from datetime import datetime
from typing import Type

from beanie import Document, Indexed
from beanie.operators import Set
from typing_extensions import Annotated

from backend.core.dto import AbstractDTO
from backend.core.utils import get_current_time
from backend.repository.base import EntityNotFoundError, IMapper, IRepository


class AbstractMongoModel(Document):
    uuid: Annotated[str, Indexed(unique=True)]
    created_at: datetime | None
    deleted_at: datetime | None


class AbstractMongoMapper[DtoT: AbstractDTO, ModelT: AbstractMongoModel](
    IMapper[DtoT, ModelT]
):
    ...


class AbstractMongoRepository[DtoT: AbstractDTO, ModelT: AbstractMongoModel](
    IRepository[DtoT]
):
    model: Type[ModelT]
    mapper: AbstractMongoMapper[DtoT, ModelT]

    async def get(self, uuid: str) -> DtoT:
        if result := await self.model.find_one(
            self.model.uuid == uuid, self.model.deleted_at == None
        ):
            return self.mapper.from_model(model=result)

        raise EntityNotFoundError(uuid)

    async def save(self, data: DtoT) -> DtoT:
        model = self.mapper.to_model(dto=data)
        await self.model.find_one(self.model.uuid == data.uuid).upsert(
            Set(model.model_dump()), on_insert=model
        )
        return self.mapper.from_model(model=model)

    async def delete(self, uuid: str) -> DtoT:
        if result := await self.model.find_one(self.model.uuid == uuid):
            await result.update(Set(self.model.deleted_at == get_current_time()))

            if updated_result := await self.model.get(document_id=result.id):
                return self.mapper.from_model(model=updated_result)

        raise EntityNotFoundError(uuid)
