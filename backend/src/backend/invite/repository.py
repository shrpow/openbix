# ruff: noqa: E711

from beanie import SortDirection

from backend.invite.dto import InviteDTO
from backend.invite.models import InviteModel
from backend.repository.mongo import AbstractMongoMapper, AbstractMongoRepository


class InviteNotExistsError(Exception):
    ...


class InviteMapper(AbstractMongoMapper[InviteDTO, InviteModel]):
    def from_model(self, model: InviteModel) -> InviteDTO:
        return InviteDTO(
            uuid=model.uuid,
            created_at=model.created_at,
            deleted_at=model.deleted_at,
            invited_user_id=model.invited_user_id,
            invitee_user_id=model.invitee_user_id,
        )

    def to_model(self, dto: InviteDTO) -> InviteModel:
        return InviteModel(
            uuid=dto.uuid,
            created_at=dto.created_at,
            deleted_at=dto.deleted_at,
            invited_user_id=dto.invited_user_id,
            invitee_user_id=dto.invitee_user_id,
        )


class InviteRepository(AbstractMongoRepository[InviteDTO, InviteModel]):
    model = InviteModel
    mapper: InviteMapper = InviteMapper()

    async def is_invitee_exists(self, invitee_user_id: str) -> bool:
        return bool(
            await self.model.find_one(
                self.model.invitee_user_id == invitee_user_id,
                self.model.deleted_at == None,
            )
        )

    async def get_invitee_count(self, invited_user_id: str) -> int:
        return await self.model.find(
            self.model.invited_user_id == invited_user_id
        ).count()

    async def find(
        self,
        invited_user_id: str | None = None,
        invitee_user_id: str | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> list[InviteDTO]:
        criteria = (
            []
            + (
                []
                if invited_user_id is None
                else [self.model.invited_user_id == invited_user_id]
            )
            + (
                []
                if invitee_user_id is None
                else [self.model.invitee_user_id == invitee_user_id]
            )
            + [self.model.deleted_at == None]
        )

        return [
            self.mapper.from_model(model=invite)
            async for invite in self.model.find(
                *criteria, skip=offset, limit=limit
            ).sort((self.model.created_at, SortDirection.DESCENDING))
        ]
