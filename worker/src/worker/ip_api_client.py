from abc import ABC, abstractmethod
from dataclasses import dataclass

from worker.network_client import INetworkClient, Request


@dataclass(frozen=True, slots=True)
class IpInfo:
    ip: str
    timezone: str


class IIpApiClient(ABC):
    @abstractmethod
    async def get_current_ip_info(self) -> IpInfo:
        ...


class IpApiClient(IIpApiClient):
    API_ENDPOINT = "https://demo.ip-api.com/json/"
    __network_client: INetworkClient

    def __init__(self, network_client: INetworkClient) -> None:
        self.__network_client = network_client

    async def get_current_ip_info(self) -> IpInfo:
        resp = await self.__network_client.send_request(
            request=Request(
                method="GET",
                url=self.API_ENDPOINT,
                headers={
                    "Origin": "https://ip-api.com",
                    "Referer": "https://ip-api.com/",
                },
            )
        )
        resp_json = resp.json()
        return IpInfo(ip=resp_json["query"], timezone=resp_json["timezone"])
