from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AbstractEntity(ABC):
    uuid: str
    created_at: datetime | None
    deleted_at: datetime | None

    @staticmethod
    @abstractmethod
    def create(*args, **kwargs) -> "AbstractEntity":
        raise NotImplementedError

    @abstractmethod
    def update(self, *args, **kwargs) -> "AbstractEntity":
        raise NotImplementedError
