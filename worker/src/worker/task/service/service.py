import asyncio
import sys
import traceback
from datetime import datetime

import pytz
from loguru import logger

from worker.captcha.service import CaptchaService
from worker.captcha_recognition_client import TwoCaptchaRecognitionClient
from worker.commonservice_client import CommonserviceClient
from worker.config import Config
from worker.emq.service import ExternalMQService
from worker.event_bus import EventBus, EventType
from worker.game.service.service import GameService
from worker.ip_api_client import IpApiClient
from worker.moonbix_client import MoonbixClient
from worker.network_client import NetworkClient
from worker.task.service.messages import (
    InternalErrorMessage,
    InvalidGameAccountMessage,
    NewTaskMessage,
    TaskResultMessage,
)


class InvalidGameAccountError(Exception):
    ...


class TaskService:
    __event_bus: EventBus
    __emq_service: ExternalMQService
    # __tasks: list[asyncio.Task]

    def __init__(self, event_bus: EventBus, emq_service: ExternalMQService) -> None:
        self.__event_bus = event_bus
        self.__emq_service = emq_service
        # self.__tasks = []

        self.__emq_service.on_message(
            message_type=NewTaskMessage, callback=self.on_new_task_message
        )
        self.__event_bus.on_event(
            event_type=EventType.STOP_WORK, callback=self.on_stop_work_event
        )

    async def on_stop_work_event(self, payload: None) -> None:
        # for task in self.__tasks:
        #     task.cancel()
        logger.error("niggers are terminating...")
        sys.exit(1)

    async def process_task(self, task: NewTaskMessage) -> None:
        network_client = NetworkClient(proxy=task.proxy)
        ip_api_client = IpApiClient(network_client=network_client)
        moonbix_client = MoonbixClient(network_client=network_client)
        captcha_service = CaptchaService(
            captcha_recognition_service=TwoCaptchaRecognitionClient(
                network_client=network_client,
                api_key=task.captcha_recognition_provider_api_key,
            ),
            commonservice_client=CommonserviceClient(network_client=network_client),
        )

        try:
            ip_info = await ip_api_client.get_current_ip_info()
            logger.debug(f"{task=} got ip_info")

            m_access_token = await moonbix_client.get_token(auth_data=task.auth_data)
        except Exception:
            raise InvalidGameAccountError()

        m_daily_reward_claim_result = await moonbix_client.complete_task(
            access_token=m_access_token, resource_id=2057
        )

        if m_daily_reward_claim_result:
            logger.debug(f"{task=} {m_daily_reward_claim_result=}")
        else:
            logger.error(f"{task=} {m_daily_reward_claim_result=}")

        for _ in range(6):
            m_user = await moonbix_client.get_user(access_token=m_access_token)

            if m_user.is_banned:
                logger.debug(f"{task=} canceled earlier due to ban")
                raise InvalidGameAccountError()

            if not m_user.available_attempts:
                logger.debug(
                    f"{task=} canceled earlier due to lack of available attempts"
                )
                break

            game = GameService(
                moonbix_client=moonbix_client, captcha_service=captcha_service
            )
            current_local_time = round(
                datetime.now(tz=pytz.timezone(zone=ip_info.timezone)).timestamp() * 1000
            )
            logger.debug(f"{task=} will play game now")
            result = await game.play_game(
                access_token=m_access_token,
                telegram_user_id=int(task.auth_data.split("%3A")[1].split("%2C")[0]),
                start_timestamp=current_local_time,
                duration=45,
            )
            logger.debug(f"{task=} {result=}")

            m_user_after_game = await moonbix_client.get_user(
                access_token=m_access_token
            )

            if (
                not (server_side_reward := m_user_after_game.balance - m_user.balance)
                == result.score
            ):
                logger.error(f"{task=} MISCALC {server_side_reward=} {game=} {result=}")

            asyncio.create_task(
                self.__emq_service.send_message(
                    recipient_input_address=Config.EMQ_WORKER_MESSAGE_BUS_ADDRESS,
                    message=TaskResultMessage(
                        game_account_id=task.game_account_id,
                        was_banned=not m_user.is_banned and m_user_after_game.is_banned,
                        balance=m_user_after_game.balance,
                    ),
                )
            )

        logger.debug(f"{task=} processing finished")

    async def on_new_task_message(self, data: dict) -> None:
        task = NewTaskMessage(**data)

        async def process_task() -> None:
            try:
                async with asyncio.timeout(600):
                    await self.process_task(task=task)
            except TimeoutError:
                logger.error(f"{task=} canceled due to timeout error")
            except InvalidGameAccountError:
                asyncio.create_task(
                    self.__emq_service.send_message(
                        recipient_input_address=Config.EMQ_WORKER_MESSAGE_BUS_ADDRESS,
                        message=InvalidGameAccountMessage(
                            game_account_id=task.game_account_id
                        ),
                    )
                )
            except Exception:
                asyncio.create_task(
                    self.__emq_service.send_message(
                        recipient_input_address=Config.EMQ_WORKER_MESSAGE_BUS_ADDRESS,
                        message=InternalErrorMessage(traceback=traceback.format_exc()),
                    )
                )
                logger.error(f"{task=} {traceback.format_exc()}")

        logger.debug(f"got new task {task=}")
        # self.__tasks.append(
        asyncio.create_task(process_task())
        # )

    async def start_heartbeat(self) -> None:
        while 1:
            await asyncio.sleep(10)
