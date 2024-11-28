import asyncio
from dataclasses import asdict

from beanie import init_beanie
from loguru import logger

from backend.authz.service import AuthzService
from backend.config import Config
from backend.emq.service import ExternalMQService
from backend.event_bus.service import EventBusService
from backend.game_account.models import GameAccountModel
from backend.game_account.repository import GameAccountRepository
from backend.game_account.service import GameAccountService
from backend.i18n.language import Language
from backend.invite.models import InviteModel
from backend.invite.repository import InviteRepository
from backend.invite.service import InviteService
from backend.prometheus import PrometheusService
from backend.scheduler.service import SchedulerService
from backend.subscription.core.subscription import Subscription
from backend.subscription.dto import SubscriptionDTO
from backend.subscription.models import SubscriptionModel
from backend.subscription.repository import SubscriptionRepository
from backend.subscription.service import (
    ActiveSubscriptionNotFoundError,
    SubscriptionService,
)
from backend.tariff.repository import TariffRepository
from backend.tariff.service import TariffService
from backend.task.service import TaskService
from backend.telegram.service import TelegramService
from backend.user.core.role import RoleName
from backend.user.dto import UserDTO
from backend.user.models import UserModel
from backend.user.repository import UserRepository
from backend.user.service import UserService

# TODO там где есть user_id: str нужно чекать на метч, иначе проверять перм на foreign


async def main() -> None:
    logger.debug("starting backend...")

    await init_beanie(
        connection_string=Config.DB_CONNECTION_STRING,
        document_models=[UserModel, SubscriptionModel, GameAccountModel, InviteModel],
    )

    logger.debug("db connection succeeded")

    event_bus_service = EventBusService()
    scheduler_service = SchedulerService()

    emq_service = ExternalMQService()
    asyncio.create_task(
        emq_service.start_broker(
            input_address=Config.EMQ_WORKER_BALANCER_INPUT_ADDRESS,
            output_address=Config.EMQ_WORKER_BALANCER_OUTPUT_ADDRESS,
        )
    )
    asyncio.create_task(
        emq_service.start_listener(address=Config.EMQ_WORKER_MESSAGE_BUS_ADDRESS)
    )

    authz_service = AuthzService()
    subscription_repository = SubscriptionRepository()
    tariff_repository = TariffRepository()
    tariff_service = TariffService(repository=tariff_repository)
    subscription_service = SubscriptionService(
        repository=subscription_repository,
        authz_service=authz_service,
        tariff_service=tariff_service,
        event_bus_service=event_bus_service,
    )
    invite_repository = InviteRepository()
    invite_service = InviteService(
        repository=invite_repository,
        event_bus_service=event_bus_service,
        tariff_service=tariff_service,
    )
    user_repository = UserRepository()
    user_service = UserService(
        authz_service=authz_service,
        repository=user_repository,
        event_bus_service=event_bus_service,
    )

    game_account_repository = GameAccountRepository()
    game_account_service = GameAccountService(
        repository=game_account_repository,
        authz_service=authz_service,
        event_bus_service=event_bus_service,
        emq_service=emq_service,
        scheduler_service=scheduler_service,
        tariff_service=tariff_service,
        subscription_service=subscription_service,
    )

    god = await user_repository.save(
        data=UserDTO(
            uuid="god",
            created_at=None,
            deleted_at=None,
            telegram_id=Config.TG_GOD_USER_ID,
            language=Language.EN,
            role=RoleName.ADMIN,
            balance=0,
        )
    )
    try:
        await subscription_service.get(user=god, user_id=god.uuid)
    except ActiveSubscriptionNotFoundError:
        tariff = (await tariff_repository.get_all(offset=0, limit=25))[-1]
        await subscription_repository.save(
            SubscriptionDTO(
                **asdict(
                    Subscription.create(
                        tariff_id=tariff.uuid,
                        subscription_duration=tariff.subscription_duration,
                        user_id=god.uuid,
                        paid=1337,
                    )
                )
            )
        )

    TaskService(
        user_repository=user_repository,
        subscription_repository=subscription_repository,
        game_account_repository=game_account_repository,
        event_bus_service=event_bus_service,
        emq_service=emq_service,
    )
    await game_account_service.initialize_schedules()

    telegram_service = TelegramService(
        user_service=user_service,
        subscription_service=subscription_service,
        invite_service=invite_service,
        event_bus_service=event_bus_service,
        tariff_service=tariff_service,
        game_account_service=game_account_service,
    )
    asyncio.create_task(telegram_service.start())

    prometheus_service = PrometheusService(
        event_bus_service=event_bus_service,
        user_repository=user_repository,
        game_account_repository=game_account_repository,
    )
    asyncio.create_task(prometheus_service.start_worker())
    asyncio.create_task(prometheus_service.start_server())

    while 1:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
