import urllib
import urllib.parse
from dataclasses import dataclass


class InvalidAuthDataError(Exception):
    ...


@dataclass
class AuthData:
    auth_data: str

    @staticmethod
    def from_string(full_url: str) -> "AuthData":
        if not 100 <= len(full_url) <= 2000:
            raise InvalidAuthDataError(full_url)

        try:
            payload = urllib.parse.unquote(
                full_url.strip().split("tgWebAppData=")[1].split("&tgWebAppVersion=")[0]
            )
        except IndexError:
            raise InvalidAuthDataError(full_url)

        return AuthData(auth_data=payload)
