from dataclasses import dataclass
import asyncio
from datetime import date, datetime, time, timedelta, timezone

from loguru import logger
from api import Api
from date_utils import APP_TIMEZONE
from db import get_conn, init_db, replace_mcn_quotes, replace_wallstreet_bonds


SCHEDULED_HOURS = (0, 6, 13, 18)
DEFAULT_COLLECTION_MINUTE = 17
COLLECTION_RETRY_MINUTES = (7, 17, 27, 37, 47, 57)
CAPTURE_ADVANCE_MINUTES = 120


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
    skip_reason: str | None = None


@dataclass(frozen=True)
class ScheduledCollection:
    scheduled_at: datetime
    window: CollectionWindow


@dataclass(frozen=True)
class ScheduledCollectionResult:
    scheduled_at: datetime
    result: CollectionResult


async def _with_retries(label: str, fetcher, attempts: int = 3, delay_seconds: int = 3):
    for attempt in range(1, attempts + 1):
        try:
            return await fetcher()
        except Exception as exc:
            if attempt == attempts:
                raise
            logger.warning("{} attempt {} failed: {}; retrying", label, attempt, exc)
            await asyncio.sleep(delay_seconds)


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


def _as_app_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=APP_TIMEZONE)
    return value.astimezone(APP_TIMEZONE)


def _target_at_for_capture_time(capture_at: datetime, max_delay_minutes: int = 120) -> datetime | None:
    local_capture_at = _as_app_datetime(capture_at)
    for day_offset in range(-1, 2):
        target_date = local_capture_at.date() + timedelta(days=day_offset)
        for hour in SCHEDULED_HOURS:
            target_at = datetime.combine(target_date, time(hour), tzinfo=APP_TIMEZONE)
            window_start = target_at - timedelta(minutes=CAPTURE_ADVANCE_MINUTES)
            window_end = target_at + timedelta(minutes=max_delay_minutes)
            if window_start <= local_capture_at <= window_end:
                return target_at

    return None


def _collection_window_for_target(target_at: datetime) -> CollectionWindow:
    target_at = _as_app_datetime(target_at).replace(minute=0, second=0, microsecond=0)
    hour = target_at.hour
    weekday = target_at.weekday()

    if weekday == 5 and hour != 0:
        return CollectionWindow(False, None, None, "saturday_daytime")
    if weekday == 6:
        return CollectionWindow(False, None, None, "sunday")
    if weekday == 0 and hour == 0:
        return CollectionWindow(False, None, None, "monday_00")

    record_date = (target_at - timedelta(hours=1)).date()
    return CollectionWindow(True, record_date, f"{hour:02d}:00")


def _latest_retry_at(
    window_start: datetime,
    window_end: datetime,
    now: datetime,
    collection_minutes: tuple[int, ...],
) -> datetime | None:
    latest = min(now, window_end).replace(second=0, microsecond=0)
    candidate = latest
    while candidate >= window_start:
        if candidate.minute in collection_minutes:
            return candidate
        candidate -= timedelta(minutes=1)

    return None


def is_schedule_stale(scheduled_at: datetime, now: datetime | None = None, max_delay_minutes: int = 120) -> bool:
    current = now or datetime.now(timezone.utc)
    current = _as_app_datetime(current)
    target_at = _target_at_for_capture_time(scheduled_at, max_delay_minutes=max_delay_minutes)
    if target_at is None:
        return True

    return current > target_at + timedelta(minutes=max_delay_minutes)


async def has_complete_slot(date_str: str, time_point: str) -> bool:
    async with get_conn() as conn:
        quote_row = await (
            await conn.execute(
                "SELECT COUNT(*) FROM mcn_quotes WHERE date_str = ? AND time_point = ?",
                (date_str, time_point),
            )
        ).fetchone()
        bond_row = await (
            await conn.execute(
                "SELECT COUNT(*) FROM wallstreet_bonds WHERE date_str = ? AND time_point = ?",
                (date_str, time_point),
            )
        ).fetchone()

    return quote_row[0] > 0 and bond_row[0] > 0


def collection_window(
    now: datetime | None = None,
    scheduled_hour: int | None = None,
    scheduled_at: datetime | None = None,
) -> CollectionWindow:
    local_now = scheduled_at or now or datetime.now(APP_TIMEZONE)
    local_now = _as_app_datetime(local_now)

    if scheduled_hour is not None:
        target_at = local_now.replace(hour=scheduled_hour, minute=0, second=0, microsecond=0)
        return _collection_window_for_target(target_at)

    target_at = _target_at_for_capture_time(local_now)
    if target_at is None:
        return CollectionWindow(False, None, None, "outside_capture_window")

    return _collection_window_for_target(target_at)


def recent_collection_windows(
    now: datetime | None = None,
    max_delay_minutes: int = 120,
    collection_minute: int | None = None,
) -> list[ScheduledCollection]:
    local_now = now or datetime.now(APP_TIMEZONE)
    if local_now.tzinfo is None:
        local_now = local_now.replace(tzinfo=APP_TIMEZONE)
    local_now = local_now.astimezone(APP_TIMEZONE)

    collection_minutes = (collection_minute,) if collection_minute is not None else COLLECTION_RETRY_MINUTES
    candidates_by_slot = {}
    for offset in range(-1, 2):
        candidate_date = local_now.date() + timedelta(days=offset)
        for hour in SCHEDULED_HOURS:
            target_at = datetime.combine(candidate_date, time(hour), tzinfo=APP_TIMEZONE)
            window_start = target_at - timedelta(minutes=CAPTURE_ADVANCE_MINUTES)
            window_end = target_at + timedelta(minutes=max_delay_minutes)
            if not window_start <= local_now <= window_end:
                continue

            scheduled_at = _latest_retry_at(window_start, window_end, local_now, collection_minutes)
            if scheduled_at is None:
                continue

            window = _collection_window_for_target(target_at)
            if not window.should_collect:
                continue

            slot_key = (window.record_date, window.time_point)
            current = candidates_by_slot.get(slot_key)
            if current is None or scheduled_at > current.scheduled_at:
                candidates_by_slot[slot_key] = ScheduledCollection(scheduled_at, window)

    return sorted(candidates_by_slot.values(), key=lambda candidate: candidate.scheduled_at)


async def collect_once(
    now: datetime | None = None,
    scheduled_hour: int | None = None,
    scheduled_at: datetime | None = None,
    skip_existing: bool = False,
) -> CollectionResult:
    window = collection_window(now=now, scheduled_hour=scheduled_hour, scheduled_at=scheduled_at)
    if not window.should_collect:
        return CollectionResult(window=window)

    await init_db()
    date_str = window.record_date.strftime("%Y-%m-%d")
    if skip_existing and await has_complete_slot(date_str, window.time_point):
        return CollectionResult(window=window, skip_reason="existing_slot")

    api = Api()
    quotes = await _with_retries("mcn_finance_quotes", api.mcn_finance_quotes)
    await replace_mcn_quotes(quotes, date_str, window.time_point)

    bonds = await _with_retries(
        "wallstreet_bonds",
        lambda: api.wallstreet_bonds(page=1, size=60),
    )
    await replace_wallstreet_bonds(bonds, date_str, window.time_point)

    return CollectionResult(window=window, quotes_count=len(quotes), bonds_count=len(bonds))


async def collect_missing_recent_slots(
    now: datetime | None = None,
    max_delay_minutes: int = 120,
) -> list[ScheduledCollectionResult]:
    results = []
    for candidate in recent_collection_windows(now=now, max_delay_minutes=max_delay_minutes):
        window = candidate.window
        date_str = window.record_date.strftime("%Y-%m-%d")
        if await has_complete_slot(date_str, window.time_point):
            results.append(
                ScheduledCollectionResult(
                    scheduled_at=candidate.scheduled_at,
                    result=CollectionResult(window=window, skip_reason="existing_slot"),
                )
            )
            continue

        result = await collect_once(scheduled_at=candidate.scheduled_at, skip_existing=True)
        results.append(ScheduledCollectionResult(candidate.scheduled_at, result))

    return results
