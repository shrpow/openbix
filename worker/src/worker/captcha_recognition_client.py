import asyncio
from abc import ABC, abstractmethod
from base64 import b64encode

from loguru import logger

from worker.network_client import NetworkClient, Request


class CaptchaSolverResultWaitTimeoutExceeded(Exception):
    ...


class ICaptchaRecognitionClient(ABC):
    @abstractmethod
    async def get_grid_captcha_solution(
        self, image: bytes, task_condition: str, rows_count: int, cols_count: int
    ) -> list[int]:
        raise NotImplementedError


class TwoCaptchaRecognitionClient(ICaptchaRecognitionClient):
    __api_key: str
    __network_client: NetworkClient

    def __init__(self, network_client: NetworkClient, api_key: str) -> None:
        self.__api_key = api_key
        self.__network_client = network_client

    async def get_grid_captcha_solution(
        self, image: bytes, task_condition: str, rows_count: int, cols_count: int
    ) -> list[int]:
        task_data_resp = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://api.rucaptcha.com/createTask",
                json={
                    "clientKey": self.__api_key,
                    "task": {
                        "type": "GridTask",
                        "body": b64encode(image).decode(),
                        # "imgType": "recaptcha",
                        "rows": rows_count,
                        "columns": cols_count,
                        "comment": task_condition,
                    },
                },
            )
        )
        task_id = task_data_resp.json()["taskId"]

        for _ in range(10):
            task_result_resp = await self.__network_client.send_request(
                request=Request(
                    method="POST",
                    url="https://api.rucaptcha.com/getTaskResult",
                    json={"clientKey": self.__api_key, "taskId": task_id},
                )
            )

            try:
                task_result: list[int] = task_result_resp.json()["solution"]["click"]
                return task_result
            except KeyError:
                logger.debug("sleeping")
                await asyncio.sleep(10)

        raise CaptchaSolverResultWaitTimeoutExceeded()
