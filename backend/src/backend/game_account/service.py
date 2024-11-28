import asyncio
from dataclasses import asdict

from loguru import logger

from backend.authz.service import AuthzService
from backend.core.utils import get_current_time
from backend.emq.service import ExternalMQService
from backend.event_bus.service import EventBusService
from backend.game_account.core.game_account import GameAccount
from backend.game_account.core.status import Status
from backend.game_account.dto import GameAccountDTO
from backend.game_account.events import (
    GameAccountReadyForProcessingEvent,
    UpdateGameAccountEvent,
)
from backend.game_account.messages import InvalidGameAccountMessage
from backend.game_account.repository import GameAccountRepository
from backend.scheduler.core.job import SchedulerJob
from backend.scheduler.service import SchedulerService
from backend.subscription.service import (
    ActiveSubscriptionNotFoundError,
    SubscriptionService,
)
from backend.tariff.service import TariffService
from backend.user.core.role import Permission
from backend.user.dto import UserDTO


class GameAccountCannotBeCreatedError(Exception):
    ...


class GameAccountAlreadyExistsError(Exception):
    ...


class GameAccountService:
    __repository: GameAccountRepository
    __authz_service: AuthzService
    __tariff_service: TariffService
    __subscription_service: SubscriptionService
    __event_bus_service: EventBusService
    __emq_service: ExternalMQService
    __scheduler_service: SchedulerService  # тут этого не должно быть

    def __init__(
        self,
        repository: GameAccountRepository,
        authz_service: AuthzService,
        tariff_service: TariffService,
        subscription_service: SubscriptionService,
        event_bus_service: EventBusService,
        emq_service: ExternalMQService,
        scheduler_service: SchedulerService,
    ) -> None:
        self.__repository = repository
        self.__authz_service = authz_service
        self.__tariff_service = tariff_service
        self.__subscription_service = subscription_service
        self.__event_bus_service = event_bus_service
        self.__emq_service = emq_service
        self.__scheduler_service = scheduler_service  #  нахуй оно тут блядь

        self.__event_bus_service.on_event(
            event_type=UpdateGameAccountEvent,
            callback=self.on_update_game_account_event,
        )

        self.__emq_service.on_message(
            message_type=InvalidGameAccountMessage,
            callback=self.on_invalid_game_account_message,
        )

    async def on_invalid_game_account_message(self, data: dict) -> None:
        message = InvalidGameAccountMessage(**data)
        logger.error(f"{message=} game account is invalid")
        game_account = GameAccount(
            **asdict(await self.__repository.get(uuid=message.game_account_id))
        )
        game_account.update(status=Status.INACTIVE, last_login_at=None, balance=None)
        await self.__repository.save(data=GameAccountDTO(**asdict(game_account)))

    async def on_update_game_account_event(self, event: UpdateGameAccountEvent) -> None:
        game_account = GameAccount(
            **asdict(await self.__repository.get(uuid=event.game_account_id))
        )
        game_account.update(
            status=Status.INACTIVE if event.is_invalid else None,
            last_login_at=event.last_login_at,
            balance=event.balance,
        )
        await self.__repository.save(data=GameAccountDTO(**asdict(game_account)))

    async def is_possible_to_create(self, user: UserDTO, user_id: str) -> bool:
        try:
            subscription = await self.__subscription_service.get(
                user=user, user_id=user_id
            )
        except ActiveSubscriptionNotFoundError:
            return False

        tariff_details = await self.__tariff_service.get(uuid=subscription.tariff_id)
        active_game_accounts_count, total_game_accounts_count = await asyncio.gather(
            self.__repository.count_by_user(user_id=user_id, status=Status.ACTIVE),
            self.__repository.count_by_user(user_id=user_id, status=None),
        )

        if (active_game_accounts_count + 1 > tariff_details.max_game_accounts) or (
            total_game_accounts_count + 1 > 1000
        ):
            return False

        return True

    async def create_preview(
        self,
        user: UserDTO,
        user_id: str,
        name: str,
        full_url: str,
        proxy: str,
        captcha_recognition_provider_api_key: str,
    ) -> GameAccountDTO:
        self.__authz_service.check_permissions(
            user=user, permissions=[Permission.UPDATE_GAME_ACCOUNTS]
        )
        game_account = GameAccount.create(
            user_id=user_id,
            name=name,
            full_url=full_url,
            proxy=proxy,
            captcha_recognition_provider_api_key=captcha_recognition_provider_api_key,
        )
        return GameAccountDTO(**asdict(game_account))

    async def create(
        self,
        user: UserDTO,
        user_id: str,
        name: str,
        full_url: str,
        proxy: str,
        captcha_recognition_provider_api_key: str,
    ) -> GameAccountDTO:
        self.__authz_service.check_permissions(
            user=user, permissions=[Permission.UPDATE_GAME_ACCOUNTS]
        )

        if not await self.is_possible_to_create(user=user, user_id=user_id):
            raise GameAccountCannotBeCreatedError(full_url)

        game_account = GameAccount.create(
            user_id=user_id,
            name=name,
            full_url=full_url,
            proxy=proxy,
            captcha_recognition_provider_api_key=captcha_recognition_provider_api_key,
        )

        if await self.__repository.is_exists(auth_data=game_account.auth_data):
            raise GameAccountAlreadyExistsError(full_url)

        game_account_dto = GameAccountDTO(**asdict(game_account))
        await self.__repository.save(game_account_dto)

        await self.schedule_game_account_processing(
            game_account_id=game_account.uuid, run_immediately=True
        )

        return game_account_dto

    async def get_count(self, user: UserDTO, user_id: str) -> int:
        return await self.__repository.count_by_user(user_id=user_id)

    async def get_all(
        self, user: UserDTO, user_id: str, offset: int = 0, limit: int = 25
    ) -> list[GameAccountDTO]:
        self.__authz_service.check_permissions(
            user=user, permissions=[Permission.UPDATE_GAME_ACCOUNTS]
        )
        await self.__subscription_service.get(user=user, user_id=user_id)
        return await self.__repository.find(user_id=user_id, offset=offset, limit=limit)

    async def get(self, user: UserDTO, uuid: str) -> GameAccountDTO:
        self.__authz_service.check_permissions(
            user=user, permissions=[Permission.UPDATE_GAME_ACCOUNTS]
        )
        await self.__subscription_service.get(user=user, user_id=user.uuid)
        return await self.__repository.get(uuid=uuid)

    async def schedule_game_account_processing(
        self, game_account_id: str, run_immediately: bool
    ) -> None:
        asyncio.create_task(
            self.__scheduler_service.schedule_job(
                job=SchedulerJob.create(
                    function=self.__event_bus_service.emit,
                    kwargs={
                        "event": GameAccountReadyForProcessingEvent(
                            game_account_id=game_account_id,
                            created_at=get_current_time(),
                        )
                    },
                    run_immediately=run_immediately,
                )
            )
        )

    async def initialize_schedules(self) -> None:
        offset = 0
        batch_size = 1000

        while 1:
            accounts = await self.__repository.find(
                status=Status.ACTIVE, offset=offset, limit=batch_size
            )
            for account in accounts:
                await self.schedule_game_account_processing(
                    game_account_id=account.uuid, run_immediately=False
                )

            if len(accounts) < batch_size:
                break
            offset += len(accounts)

        logger.info(f"schedules are initialized; {offset=}")
