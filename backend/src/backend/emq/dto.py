from dataclasses import dataclass


@dataclass
class EMQMessageDTO:
    type: str
    message: dict
