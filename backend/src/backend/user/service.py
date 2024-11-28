import asyncio
from dataclasses import asdict

from backend.authz.service import AuthzService
from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.i18n.language import Language
from backend.invite.events import (
    AddInviteRewardEvent,
    NewInvitedUserEvent,
    WithdrawBalanceEvent,
)
from backend.repository.base import EntityNotFoundError
from backend.user.core.role import Permission, RoleName
from backend.user.core.user import User
from backend.user.dto import UserDTO
from backend.user.repository import UserRepository


class UserAlreadyExistsError(Exception):
    ...


class UserNotExistsError(Exception):
    ...


class UserService:
    __repository: UserRepository
    __authz_service: AuthzService
    __event_bus_service: EventBusService

    def __init__(
        self,
        repository: UserRepository,
        authz_service: AuthzService,
        event_bus_service: EventBusService,
    ) -> None:
        self.__repository = repository
        self.__authz_service = authz_service
        self.__event_bus_service = event_bus_service

        self.__event_bus_service.on_event(
            event_type=WithdrawBalanceEvent, callback=self.on_withdraw_balance
        )
        self.__event_bus_service.on_event(
            event_type=AddInviteRewardEvent, callback=self.on_invite_reward
        )

    async def create(
        self, telegram_id: int, language: Language, invited_user_id: str | None = None
    ) -> UserDTO:
        if await self.__repository.is_user_exists(telegram_id=telegram_id):
            raise UserAlreadyExistsError(telegram_id)

        user = User.create(telegram_id=telegram_id, language=language)
        user_dto = UserDTO(**asdict(user))

        await self.__repository.save(data=user_dto)

        asyncio.create_task(
            self.__event_bus_service.emit(
                event=NewInvitedUserEvent(
                    created_at=get_current_time(),
                    invited_user_id=invited_user_id,
                    invitee_user_id=user.uuid,
                )
            )
        )

        return user_dto

    async def update(
        self,
        user: UserDTO,
        user_id: str,
        language: Language | None = None,
        role: RoleName | None = None,
    ) -> UserDTO:
        if not user.uuid == user_id:
            await self.__authz_service.check_permissions(
                user=user, permissions=[Permission.UPDATE_USERS]
            )

        updatable_user = User(**asdict(await self.__repository.get(uuid=user_id)))
        updatable_user.update(language=language, role=role)

        return await self.__repository.save(data=UserDTO(**asdict(updatable_user)))

    async def find_by_telegram_id(self, telegram_id: int) -> UserDTO:
        if users := await self.__repository.find(telegram_id=telegram_id):
            return users[0]

        raise UserNotExistsError(telegram_id)

    async def get_by_id(self, user: UserDTO, uuid: str) -> UserDTO:
        if not user.uuid == uuid:
            self.__authz_service.check_permissions(  # TODO READ_FOREIGN
                user=user, permissions=[Permission.UPDATE_USERS]
            )

        try:
            return await self.__repository.get(uuid=uuid)
        except EntityNotFoundError:
            raise UserNotExistsError(uuid)

    async def on_withdraw_balance(self, event: WithdrawBalanceEvent) -> None:
        user = User(**asdict(await self.__repository.get(uuid=event.user_id)))
        user.update(balance=user.balance - event.amount)
        await self.__repository.save(data=UserDTO(**asdict(user)))

    async def on_invite_reward(self, event: AddInviteRewardEvent) -> None:
        user = User(**asdict(await self.__repository.get(uuid=event.user_id)))
        user.update(balance=user.balance + event.reward)
        await self.__repository.save(data=UserDTO(**asdict(user)))
