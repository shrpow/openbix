import enum
from dataclasses import dataclass

from worker.captcha.dto import CaptchaResultDTO
from worker.game.service.dto import GameResultDTO
from worker.network_client import INetworkClient, Request

"""
    User DTOs
"""


@dataclass(frozen=True, slots=True)
class MUserDTO:
    balance: int
    is_banned: bool
    available_attempts: int
    seconds_until_next_attempt: int


"""
    Game DTOs
"""


class MGameObjectType(enum.IntEnum):
    TRAP = 0
    REWARD = 1
    BONUS = 2


"""
    Exceptions
"""


class CaptchaNeededError(Exception):
    session_id: str

    def __init__(self, *args: object, session_id: str) -> None:
        super().__init__(*args)
        self.session_id = session_id


@dataclass(frozen=True, slots=True)
class MGameMapObject:
    type: MGameObjectType
    size: int
    reward: int
    speed: int


@dataclass(frozen=True, slots=True)
class MGameDTO:
    tag: str
    map_: list[MGameMapObject]


class MoonbixClient:
    __network_client: INetworkClient

    def __init__(self, network_client: INetworkClient) -> None:
        self.__network_client = network_client

    async def get_token(self, auth_data: str) -> str:
        response = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://www.binance.com/bapi/growth/v1/friendly/growth-paas/third-party/access/accessToken",
                headers={
                    "origin": "https://www.binance.com",
                    "referer": "https://www.binance.com/en/game/tg/moon-bix",
                },
                json={"queryString": auth_data, "socialType": "telegram"},
            )
        )
        return response.json()["data"]["accessToken"]

    async def get_user(self, access_token: str) -> MUserDTO:
        response = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://www.binance.com/bapi/growth/v1/friendly/growth-paas/mini-app-activity/third-party/user/user-info",
                headers={
                    "origin": "https://www.binance.com",
                    "referer": "https://www.binance.com/en/game/tg/moon-bix",
                    "x-growth-token": access_token,
                },
                json={"resourceId": 2056},
            )
        )
        response_json = response.json()
        seconds_until_next_attempt = (
            response_json["data"]["metaInfo"]["attemptRefreshCountDownTime"] or 0
        ) // 1000

        return MUserDTO(
            balance=response_json["data"]["metaInfo"]["totalGrade"],
            is_banned=not response_json["data"]["qualified"],
            available_attempts=(
                response_json["data"]["metaInfo"]["totalAttempts"]
                - response_json["data"]["metaInfo"]["consumedAttempts"]
            ),
            seconds_until_next_attempt=seconds_until_next_attempt,
        )

    async def get_game(
        self,
        access_token: str,
        telegram_user_id: int,
        captcha_data: CaptchaResultDTO | None,
    ) -> MGameDTO:
        response = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://www.binance.com/bapi/growth/v1/friendly/growth-paas/mini-app-activity/third-party/game/start",
                headers={
                    "origin": "https://www.binance.com",
                    "referer": "https://www.binance.com/en/game/tg/moon-bix",
                    "x-growth-token": access_token,
                    "x-tg-user-id": telegram_user_id,
                }
                | (
                    {}
                    if captcha_data is None
                    else {
                        "x-captcha-session-id": captcha_data.session_id,
                        "x-captcha-token": captcha_data.token,
                        "x-captcha-challenge": captcha_data.challenge,
                    }
                ),
                json={"resourceId": 2056},
            )
        )

        response_json = response.json()

        if "captchaverification" in response.text.lower():
            raise CaptchaNeededError(session_id=response_json["data"].get("sessionId"))

        map_: list[MGameMapObject] = []
        for map_item in response_json["data"]["cryptoMinerConfig"]["itemSettingList"]:
            for reward in map_item["rewardValueList"]:
                map_.append(
                    MGameMapObject(
                        type=MGameObjectType[map_item["type"]],
                        size=map_item["size"],
                        reward=reward,
                        speed=map_item["speed"],
                    )
                )

        return MGameDTO(tag=response_json["data"]["gameTag"], map_=map_)

    async def complete_game(self, access_token: str, result: GameResultDTO) -> bool:
        response = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://www.binance.com/bapi/growth/v1/friendly/growth-paas/mini-app-activity/third-party/game/complete",
                headers={
                    "origin": "https://www.binance.com",
                    "referer": "https://www.binance.com/en/game/tg/moon-bix",
                    "x-growth-token": access_token,
                },
                json={
                    "resourceId": 2056,
                    "payload": result.encrypted_payload,
                    "log": result.score,
                },
            )
        )
        return response.json()["code"] == "000000"

    async def complete_task(self, access_token: str, resource_id: int) -> bool:
        response = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://www.binance.com/bapi/growth/v1/friendly/growth-paas/mini-app-activity/third-party/task/complete",
                headers={
                    "origin": "https://www.binance.com",
                    "referer": "https://www.binance.com/en/game/tg/moon-bix",
                    "x-growth-token": access_token,
                },
                json={"resourceIdList": [resource_id], "referralCode": None},
            )
        )
        return response.json()["code"] == "000000"
