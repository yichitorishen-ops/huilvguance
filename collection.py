from dataclasses import dataclass
from datetime import date, datetime, timedelta

from api import Api
from date_utils import APP_TIMEZONE
from db import init_db, replace_mcn_quotes, replace_wallstreet_bonds


@dataclass(frozen=True)
class CollectionWindow:
    should_collect: bool
    record_date: date | None
    time_point: str | None
    skip_reason: str | None = None


@dataclass(frozen=True)
class CollectionResult:
    window: CollectionWindow
    quotes_count: int = 0
    bonds_count: int = 0


def collection_window(now: datetime | None = None, scheduled_hour: int | None = None) -> CollectionWindow:
    local_now = now or datetime.now(APP_TIMEZONE)
    if local_now.tzinfo is None:
        local_now = local_now.replace(tzinfo=APP_TIMEZONE)
    local_now = local_now.astimezone(APP_TIMEZONE)

    hour = local_now.hour if scheduled_hour is None else scheduled_hour
    scheduled_at = local_now.replace(hour=hour, minute=0, second=0, microsecond=0)
    weekday = scheduled_at.weekday()

    if weekday == 5 and hour != 0:
        return CollectionWindow(False, None, None, "saturday_daytime")
    if weekday == 6:
        return CollectionWindow(False, None, None, "sunday")
    if weekday == 0 and hour == 0:
        return CollectionWindow(False, None, None, "monday_00")

    record_date = (scheduled_at - timedelta(hours=1)).date()
    return CollectionWindow(True, record_date, f"{hour:02d}:00")


async def collect_once(now: datetime | None = None, scheduled_hour: int | None = None) -> CollectionResult:
    window = collection_window(now=now, scheduled_hour=scheduled_hour)
    if not window.should_collect:
        return CollectionResult(window=window)

    await init_db()
    api = Api()
    date_str = window.record_date.strftime("%Y-%m-%d")

    quotes = await api.mcn_finance_quotes()
    await replace_mcn_quotes(quotes, date_str, window.time_point)

    bonds = await api.wallstreet_bonds(page=1, size=60)
    await replace_wallstreet_bonds(bonds, date_str, window.time_point)

    return CollectionResult(window=window, quotes_count=len(quotes), bonds_count=len(bonds))
