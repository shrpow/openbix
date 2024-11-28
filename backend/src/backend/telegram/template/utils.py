import re
from datetime import datetime, timedelta, timezone

from backend.i18n.container import I18nContainer


def strftime(date: datetime, format_: str = "%d.%m.%Y") -> str:
    return date.replace(tzinfo=timezone.utc).strftime(format_) + " UTC"


def simplify_hours(hours: int | None) -> I18nContainer:
    if hours is None:
        return I18nContainer(ru="∞", en="∞")

    if (days := hours // 24) >= 1:
        return I18nContainer(ru=f"{days} д.", en=f"{days} d.")

    return I18nContainer(ru=f"{hours} ч.", en=f"{hours} h.")


def prettify_timedelta(delta: timedelta) -> I18nContainer:
    days, hours, minutes = delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60

    parts: list[I18nContainer] = (
        []
        + ([I18nContainer(ru=f"{days} д.", en=f"{days} d.")] if days else [])
        + ([I18nContainer(ru=f"{hours} ч.", en=f"{hours} h.")] if hours else [])
        + ([I18nContainer(ru=f"{minutes} мин.", en=f"{minutes} m.")] if minutes else [])
        + (
            [I18nContainer(ru="Мгновение", en="A moment")]
            if not days and not hours and not minutes
            else []
        )
    )
    return I18nContainer(
        ru=" ".join([part.ru for part in parts]),
        en=" ".join([part.en for part in parts]),
    )


def to_skeleton(content: str, placeholder: str) -> str:
    minified_content = re.sub(
        pattern=r"\{([^}]+)\}", repl=placeholder * 3, string=content
    ).strip()
    skeleton_content: list[str] = []

    for string in minified_content.splitlines():
        skeleton_content.append(placeholder * (len(string) // 2))

    return "\n".join(skeleton_content)
