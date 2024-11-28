from dataclasses import dataclass
from datetime import datetime


@dataclass
class AbstractEvent:
    created_at: datetime
