from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CaptchaResultDTO:
    session_id: str
    token: str
    challenge: str
