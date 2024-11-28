from backend.tariff.dto import TariffDTO
from backend.tariff.repository import TariffRepository


class TariffService:
    __repository: TariffRepository

    def __init__(self, repository: TariffRepository) -> None:
        self.__repository = repository

    async def get_all(self, offset: int = 0, limit: int = 25) -> list[TariffDTO]:
        return await self.__repository.get_all(offset=offset, limit=limit)

    async def get(self, uuid: str) -> TariffDTO:
        return await self.__repository.get(uuid=uuid)
