import asyncio
from dataclasses import asdict

from loguru import logger

from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.invite.core.invite import Invite
from backend.invite.dto import InviteDTO
from backend.invite.events import (
    AddInviteRewardEvent,
    NewInvitedUserEvent,
    NewInviteEvent,
)
from backend.invite.repository import InviteRepository
from backend.subscription.events import SubscriptionCreatedEvent
from backend.tariff.service import TariffService
from backend.user.dto import UserDTO


class InviteeAlreadyInvitedError(Exception):
    ...


class InviteNotExistsError(Exception):
    ...


class InviteService:
    INVITE_REWARD_PERCENT = 10

    __repository: InviteRepository
    __event_bus_service: EventBusService
    __tariff_service: TariffService

    def __init__(
        self,
        repository: InviteRepository,
        event_bus_service: EventBusService,
        tariff_service: TariffService,
    ) -> None:
        self.__repository = repository
        self.__event_bus_service = event_bus_service
        self.__tariff_service = tariff_service

        self.__event_bus_service.on_event(
            event_type=NewInvitedUserEvent, callback=self.on_invite
        )
        self.__event_bus_service.on_event(
            event_type=SubscriptionCreatedEvent, callback=self.on_subscription
        )

    async def get_invitee_count(self, user: UserDTO, invited_user_id: str) -> int:
        return await self.__repository.get_invitee_count(
            invited_user_id=invited_user_id
        )

    async def on_invite(self, event: NewInvitedUserEvent) -> None:
        try:
            await self.process_invite(
                invited_user_id=event.invited_user_id,
                invitee_user_id=event.invitee_user_id,
            )
        except InviteeAlreadyInvitedError:
            logger.debug(f"{event=} user already invited")

    async def process_invite(
        self, invited_user_id: str | None, invitee_user_id: str
    ) -> InviteDTO:
        invite = Invite.create(
            invited_user_id=invited_user_id, invitee_user_id=invitee_user_id
        )

        if await self.__repository.is_invitee_exists(
            invitee_user_id=invite.invitee_user_id
        ):
            raise InviteeAlreadyInvitedError(invite.invitee_user_id)

        invite_dto = InviteDTO(**asdict(invite))
        await self.__repository.save(data=invite_dto)

        asyncio.create_task(
            self.__event_bus_service.emit(
                event=NewInviteEvent(created_at=get_current_time())
            )
        )

        return invite_dto

    async def on_subscription(self, event: SubscriptionCreatedEvent) -> None:
        try:
            await self.process_invite_reward(
                user_id=event.subscription.user_id,
                tariff_id=event.subscription.tariff_id,
            )
        except InviteNotExistsError:
            logger.debug(f"{event=} user is not invited")

    async def process_invite_reward(self, user_id: str, tariff_id: str) -> None:
        if not (invites := await self.__repository.find(invitee_user_id=user_id)):
            raise InviteNotExistsError(user_id)

        if (invite := invites[0]).invited_user_id is None:
            return None

        tariff = await self.__tariff_service.get(uuid=tariff_id)

        asyncio.create_task(
            self.__event_bus_service.emit(
                event=AddInviteRewardEvent(
                    created_at=get_current_time(),
                    user_id=invite.invited_user_id,
                    reward=round(self.INVITE_REWARD_PERCENT * (1 / 100) * tariff.price),
                )
            )
        )
