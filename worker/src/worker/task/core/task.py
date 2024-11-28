from dataclasses import dataclass


@dataclass(slots=True)
class Task:
    auth_data: str
    proxy: str
