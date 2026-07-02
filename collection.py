from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

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


def _parse_cron_field(field: str, minimum: int, maximum: int):
    if field == "*":
        return set(range(minimum, maximum + 1))

    values = set()
    for part in field.split(","):
        if "-" in part:
            start, end = [int(piece) for piece in part.split("-", 1)]
            values.update(range(start, end + 1))
        else:
            values.add(int(part))
    return values


def latest_cron_datetime(cron_expression: str, now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc).replace(second=0, microsecond=0)

    minute_field, hour_field, _dom, _month, weekday_field = cron_expression.split()
    minutes = _parse_cron_field(minute_field, 0, 59)
    hours = _parse_cron_field(hour_field, 0, 23)
    weekdays = _parse_cron_field(weekday_field, 0, 6)

    candidate = current
    for _ in range(8 * 24 * 60):
        github_weekday = (candidate.weekday() + 1) % 7
        if candidate.minute in minutes and candidate.hour in hours and github_weekday in weekdays:
            return candidate
        candidate -= timedelta(minutes=1)

    raise ValueError(f"No recent schedule matched cron expression: {cron_expression}")


def is_schedule_stale(scheduled_at: datetime, now: datetime | None = None, max_delay_minutes: int = 120) -> bool:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)

    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    scheduled_at = scheduled_at.astimezone(timezone.utc)

    return current - scheduled_at > timedelta(minutes=max_delay_minutes)


def collection_window(
    now: datetime | None = None,
    scheduled_hour: int | None = None,
    scheduled_at: datetime | None = None,
) -> CollectionWindow:
    local_now = scheduled_at or now or datetime.now(APP_TIMEZONE)
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


async def collect_once(
    now: datetime | None = None,
    scheduled_hour: int | None = None,
    scheduled_at: datetime | None = None,
) -> CollectionResult:
    window = collection_window(now=now, scheduled_hour=scheduled_hour, scheduled_at=scheduled_at)
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
