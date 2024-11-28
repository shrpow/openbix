import ipaddress
import re
from dataclasses import dataclass

PROXY_REGEX = re.compile(
    r"(?:^|[^\dA-Za-z])(?:(?P<protocol>https?|socks[45]):\/\/)?(?:(?P<username>[\dA-Za-z]*):(?P<password>[\dA-Za-z]*)@)?(?P<host>(?:[\-\.\dA-Za-z]+|(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])(?:\.(?:\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])){3})):(?P<port>\d|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])(?=[^\dA-Za-z]|$)",
    flags=re.MULTILINE | re.IGNORECASE,
)


class InvalidProxyError(Exception):
    ...


@dataclass
class Proxy:
    protocol: str
    username: str | None
    password: str | None
    host: str
    port: str

    @staticmethod
    def validate_host(host: str) -> None:
        host_ipaddress = ipaddress.IPv4Address(host)

        if not host_ipaddress.is_global:
            raise InvalidProxyError(host)

    @staticmethod
    def from_string(proxy: str) -> "Proxy":
        if not (match_ := PROXY_REGEX.match(string=proxy.strip())):
            raise InvalidProxyError(proxy)

        protocol = match_.group("protocol") or None
        username = match_.group("username") or None
        password = match_.group("password") or None
        host = match_.group("host") or None
        port = match_.group("port") or None

        if (
            protocol is None
            or host is None
            or port is None
            or len(username or "") > 100
            or len(password or "") > 100
            or int(port) > 65535
        ):
            raise InvalidProxyError(proxy)

        Proxy.validate_host(host=host)

        return Proxy(
            protocol=protocol,
            username=username,
            password=password,
            host=host,
            port=port,
        )

    def as_string(self) -> str:
        auth_info = (
            ""
            if self.username is None and self.password is None
            else f"{self.username}:{self.password}@"
        )
        return f"{self.protocol}://{auth_info}{self.host}:{self.port}"
