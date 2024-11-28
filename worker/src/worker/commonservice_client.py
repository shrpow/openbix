from dataclasses import dataclass

from worker.network_client import INetworkClient, Request


@dataclass(frozen=True, slots=True)
class CaptchaDTO:
    image_path: str
    signature: str
    salt: str
    encryption_key: str
    task_condition: str


class CommonserviceClient:
    __network_client: INetworkClient

    def __init__(self, network_client: INetworkClient) -> None:
        self.__network_client = network_client

    async def download_captcha_image(self, image_url: str) -> bytes:
        resp = await self.__network_client.send_request(
            request=Request(method="GET", url=image_url)
        )
        return resp.bytes

    async def get_captcha(self, session_id: str) -> CaptchaDTO:
        response = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://api.commonservice.io/gateway-api/v1/public/antibot/getCaptcha",
                headers={"Content-Type": "text/plain", "x-captcha-se": "true"},
                text=f"bizId=tg_mini_game_play&sv=20220812&lang=en&securityCheckResponseValidateId={session_id}&clientType=web",
            )
        )
        response_json = response.json()
        return CaptchaDTO(
            image_path=response_json["data"]["path2"],
            signature=response_json["data"]["sig"],
            salt=response_json["data"]["salt"],
            encryption_key=response_json["data"]["ek"],
            task_condition=response_json["data"]["tag"],
        )

    async def validate_captcha(
        self,
        solution: str,
    ) -> str:
        response = await self.__network_client.send_request(
            request=Request(
                method="POST",
                url="https://api.commonservice.io/gateway-api/v1/public/antibot/validateCaptcha",
                headers={
                    "Content-Type": "text/plain",
                    "x-captcha-se": "true",
                    "clienttype": "web",
                    "fvideo-id": "xxx",
                    "bnc-uuid": "xxx",
                },
                text=solution,
            )
        )
        response_json = response.json()
        return response_json["data"]["token"]
