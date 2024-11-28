import uuid
from datetime import datetime, timezone


def get_current_time() -> datetime:
    return datetime.now(tz=timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())
