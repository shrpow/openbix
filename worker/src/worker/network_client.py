import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from curl_cffi import requests


@dataclass
class Request:
    method: Literal["GET", "POST"]
    url: str
    headers: dict | None = None
    json: dict | None = None
    text: str | None = None


@dataclass
class Response:
    status: int
    text: str
    bytes: bytes

    def json(self) -> dict:
        return json.loads(self.text)


class INetworkClient(ABC):
    @abstractmethod
    async def send_request(self, request: Request) -> Response:
        ...


class NetworkClient(INetworkClient):
    __session: requests.AsyncSession

    def __init__(self, proxy: str | None = None) -> None:
        self.__session = requests.AsyncSession(
            timeout=60,
            verify=False,
            impersonate=random.choice(
                ["chrome", "edge", "safari", "safari_ios", "chrome_android"]
            ),
            proxy=proxy,
        )

    async def send_request(self, request: Request) -> Response:
        resp = await self.__session.request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            json=request.json,
            data=request.text,
        )
        return Response(status=resp.status_code, text=resp.text, bytes=resp.content)
