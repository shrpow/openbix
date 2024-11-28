import asyncio

from loguru import logger

from backend.config import Config
from backend.core.utils import get_current_time
from backend.emq.service import ExternalMQService
from backend.event_bus.service import EventBusService
from backend.game_account.core.status import Status
from backend.game_account.events import (
    GameAccountReadyForProcessingEvent,
    UpdateGameAccountEvent,
)
from backend.game_account.messages import InvalidGameAccountMessage
from backend.game_account.repository import GameAccountRepository
from backend.repository.base import EntityNotFoundError
from backend.subscription.repository import SubscriptionRepository
from backend.task.events import FailedTaskEvent, SuccessTaskEvent
from backend.task.messages import (
    InternalErrorMessage,
    NewTaskMessage,
    TaskResultMessage,
)
from backend.user.repository import UserRepository


class TaskService:  # перенести в game service думаю? хуёва думаеш
    __user_repository: UserRepository
    __subscription_repository: SubscriptionRepository
    __game_account_repository: GameAccountRepository
    __event_bus_service: EventBusService
    __emq_service: ExternalMQService

    def __init__(
        self,
        user_repository: UserRepository,
        subscription_repository: SubscriptionRepository,
        game_account_repository: GameAccountRepository,  # хуйня сервис прокинь
        event_bus_service: EventBusService,
        emq_service: ExternalMQService,
    ) -> None:
        self.__user_repository = user_repository
        self.__subscription_repository = subscription_repository
        self.__game_account_repository = game_account_repository
        self.__event_bus_service = event_bus_service
        self.__emq_service = emq_service

        self.__event_bus_service.on_event(
            event_type=GameAccountReadyForProcessingEvent,
            callback=self.on_ready_game_account,
        )

        self.__emq_service.on_message(
            message_type=TaskResultMessage, callback=self.on_task_result
        )
        self.__emq_service.on_message(
            message_type=InvalidGameAccountMessage, callback=self.on_game_account_error
        )
        self.__emq_service.on_message(
            message_type=InternalErrorMessage, callback=self.on_internal_error
        )

    async def on_ready_game_account(
        self, event: GameAccountReadyForProcessingEvent
    ) -> None:
        try:
            game_account = await self.__game_account_repository.get(
                uuid=event.game_account_id
            )
            user = await self.__user_repository.get(uuid=game_account.user_id)
        except EntityNotFoundError:
            logger.debug(f"{event.game_account_id=} game account or user is not found")
            return None

        if game_account.status == Status.INACTIVE:
            logger.debug(
                f"{event.game_account_id=} {game_account=} game account is inactive"
            )
            return None

        user_subscriptions = await self.__subscription_repository.find(
            user_id=user.uuid, active_until=get_current_time()
        )

        if not user_subscriptions:
            logger.debug(
                f"{event.game_account_id=} {user=} user has no active subscriptions"
            )  # TODO emit event
            return None

        asyncio.create_task(
            self.__emq_service.send_message(
                recipient_input_address=Config.EMQ_WORKER_BALANCER_INPUT_ADDRESS,
                message=NewTaskMessage(
                    game_account_id=game_account.uuid,
                    auth_data=game_account.auth_data,
                    proxy=game_account.proxy,
                    captcha_recognition_provider=game_account.captcha_recognition_provider,
                    captcha_recognition_provider_api_key=game_account.captcha_recognition_provider_api_key,
                ),
            )
        )
        logger.debug("task sent")

    async def on_task_result(self, data: dict) -> None:
        message = TaskResultMessage(**data)
        asyncio.create_task(
            self.__event_bus_service.emit(
                event=SuccessTaskEvent(created_at=get_current_time())
            )
        )
        asyncio.create_task(
            self.__event_bus_service.emit(
                event=UpdateGameAccountEvent(
                    created_at=get_current_time(),
                    game_account_id=message.game_account_id,
                    balance=message.balance,
                    is_invalid=message.was_banned,
                    last_login_at=get_current_time(),
                )
            )
        )

    async def on_game_account_error(self, data: dict) -> None:
        message = InvalidGameAccountMessage(**data)
        asyncio.create_task(
            self.__event_bus_service.emit(
                event=FailedTaskEvent(created_at=get_current_time())
            )
        )
        asyncio.create_task(
            self.__event_bus_service.emit(
                event=UpdateGameAccountEvent(
                    created_at=get_current_time(),
                    game_account_id=message.game_account_id,
                    balance=None,
                    is_invalid=True,
                    last_login_at=None,
                )
            )
        )

    async def on_internal_error(self, data: dict) -> None:
        message = InternalErrorMessage(**data)
        asyncio.create_task(
            self.__event_bus_service.emit(
                event=FailedTaskEvent(created_at=get_current_time())
            )
        )
        logger.error(message.traceback)
