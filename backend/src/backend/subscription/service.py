import asyncio
from dataclasses import asdict

from backend.authz.service import AuthzService
from backend.core.utils import get_current_time
from backend.event_bus.service import EventBusService
from backend.invite.events import WithdrawBalanceEvent
from backend.subscription.core.subscription import Subscription
from backend.subscription.dto import SubscriptionDTO
from backend.subscription.events import SubscriptionCreatedEvent
from backend.subscription.repository import SubscriptionRepository
from backend.tariff.service import TariffService
from backend.user.core.role import Permission
from backend.user.dto import UserDTO


class ActiveSubscriptionNotFoundError(Exception):
    ...


class SubscriptionService:
    __repository: SubscriptionRepository
    __authz_service: AuthzService
    __tariff_service: TariffService
    __event_bus_service: EventBusService

    def __init__(
        self,
        repository: SubscriptionRepository,
        authz_service: AuthzService,
        tariff_service: TariffService,
        event_bus_service: EventBusService,
    ) -> None:
        self.__repository = repository
        self.__authz_service = authz_service
        self.__tariff_service = tariff_service
        self.__event_bus_service = event_bus_service

    async def get(self, user: UserDTO, user_id: str) -> SubscriptionDTO:
        if not (
            subscriptions := await self.__repository.find(
                user_id=user_id, active_until=get_current_time(), limit=1
            )
        ):
            raise ActiveSubscriptionNotFoundError(user_id)

        return subscriptions[0]

    async def create_preview(
        self, user: UserDTO, tariff_id: str, user_id: str, duration: int | None
    ) -> SubscriptionDTO:
        self.__authz_service.check_permissions(
            user=user, permissions=[Permission.UPDATE_USERS]
        )
        subscription = Subscription.create(
            tariff_id=tariff_id, subscription_duration=duration, user_id=user_id, paid=0
        )
        return SubscriptionDTO(**asdict(subscription))

    async def create(
        self,
        user: UserDTO,
        tariff_id: str,
        user_id: str,
        duration: int | None,
        is_withdraw_needed: bool,
    ) -> SubscriptionDTO:
        self.__authz_service.check_permissions(
            user=user, permissions=[Permission.UPDATE_USERS]
        )
        tariff = await self.__tariff_service.get(uuid=tariff_id)
        subscription = Subscription.create(
            tariff_id=tariff_id,
            subscription_duration=duration,
            user_id=user_id,
            paid=tariff.price,
        )
        subscription_dto = SubscriptionDTO(**asdict(subscription))
        await self.__repository.save(data=subscription_dto)

        asyncio.create_task(
            self.__event_bus_service.emit(
                event=SubscriptionCreatedEvent(
                    created_at=get_current_time(),
                    issuer=user,
                    subscription=subscription_dto,
                    tariff=tariff,
                )
            )
        )

        if is_withdraw_needed:
            asyncio.create_task(
                self.__event_bus_service.emit(
                    event=WithdrawBalanceEvent(
                        created_at=get_current_time(),
                        user_id=user_id,
                        amount=tariff.price,
                    )
                )
            )

        return subscription_dto
