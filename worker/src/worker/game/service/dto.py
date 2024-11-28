from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GameResultDTO:
    encrypted_payload: str
    score: int
    plain_payload: str
    aes_iv: str
    aes_key: str
