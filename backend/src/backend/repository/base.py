from abc import ABC, abstractmethod


class EntityNotFoundError(Exception):
    ...


class IRepository[DtoT](ABC):
    @abstractmethod
    async def get(self, uuid: str) -> DtoT:
        raise NotImplementedError

    @abstractmethod
    async def save(self, data: DtoT) -> DtoT:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, uuid: str) -> DtoT:
        raise NotImplementedError


class IMapper[DtoT, ModelT](ABC):
    @abstractmethod
    def from_model(self, model: ModelT) -> DtoT:
        raise NotImplementedError

    @abstractmethod
    def to_model(self, dto: DtoT) -> ModelT:
        raise NotImplementedError
