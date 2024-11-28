import asyncio

from prometheus_client import Counter, Gauge, start_http_server

from backend.event_bus.events import EventSentEvent
from backend.event_bus.service import EventBusService
from backend.game_account.repository import GameAccountRepository
from backend.task.events import FailedTaskEvent, SuccessTaskEvent
from backend.telegram.events import UserInteractedWithBotEvent
from backend.user.repository import UserRepository


class PrometheusService:
    __event_bus_service: EventBusService
    __user_repository: UserRepository
    __game_account_repository: GameAccountRepository

    __counter_telegram_bot_interactions: Counter
    __counter_total_users: Gauge
    __counter_total_game_accounts: Gauge
    __counter_total_success_tasks: Counter
    __counter_total_failed_tasks: Counter
    __counter_total_event_bus_messages: Counter

    def __init__(
        self,
        event_bus_service: EventBusService,
        user_repository: UserRepository,
        game_account_repository: GameAccountRepository,
    ) -> None:
        self.__event_bus_service = event_bus_service
        self.__user_repository = user_repository
        self.__game_account_repository = game_account_repository

        self.__counter_telegram_bot_interactions = Counter(
            name="total_tg_bot_interactions", documentation="TG Bot interactions"
        )
        self.__counter_total_users = Gauge(name="total_users", documentation="Users")
        self.__counter_total_game_accounts = Gauge(
            name="total_game_accounts", documentation="Game Accounts"
        )
        self.__counter_total_success_tasks = Counter(
            name="total_success_tasks", documentation="Success Tasks"
        )
        self.__counter_total_failed_tasks = Counter(
            name="total_failed_tasks", documentation="Failed Tasks"
        )
        self.__counter_total_event_bus_messages = Counter(
            name="total_event_bus_messages", documentation="Event Bus Messages"
        )

        self.__event_bus_service.on_event(
            event_type=UserInteractedWithBotEvent,
            callback=self.on_user_interaction_event,
        )
        self.__event_bus_service.on_event(
            event_type=SuccessTaskEvent,
            callback=self.on_success_task_event,
        )
        self.__event_bus_service.on_event(
            event_type=FailedTaskEvent,
            callback=self.on_failed_task_event,
        )
        self.__event_bus_service.on_event(
            event_type=EventSentEvent,
            callback=self.on_any_event_bus_event,
        )

    async def on_user_interaction_event(
        self, event: UserInteractedWithBotEvent
    ) -> None:
        self.__counter_telegram_bot_interactions.inc()

    async def on_success_task_event(self, event: SuccessTaskEvent) -> None:
        self.__counter_total_success_tasks.inc()

    async def on_failed_task_event(self, event: FailedTaskEvent) -> None:
        self.__counter_total_failed_tasks.inc()

    async def on_any_event_bus_event(self, event: EventSentEvent) -> None:
        self.__counter_total_event_bus_messages.inc()

    async def count_users(self) -> None:
        self.__counter_total_users.set(await self.__user_repository.get_total_count())

    async def count_game_accounts(self) -> None:
        self.__counter_total_game_accounts.set(
            await self.__game_account_repository.get_total_count()
        )

    async def start_worker(self) -> None:
        while 1:
            await asyncio.gather(self.count_users(), self.count_game_accounts())
            await asyncio.sleep(30)

    async def start_server(self) -> None:
        await asyncio.to_thread(start_http_server, 8000)
