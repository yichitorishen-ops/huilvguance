from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo("Asia/Shanghai")


def current_app_date(now=None):
    if now is None:
        return datetime.now(APP_TIMEZONE).date()
    if isinstance(now, datetime):
        if now.tzinfo is None:
            now = now.replace(tzinfo=APP_TIMEZONE)
        return now.astimezone(APP_TIMEZONE).date()
    return now


def resolve_friday_date(friday_date=None, now=None):
    if friday_date:
        return datetime.strptime(friday_date, "%Y-%m-%d").date()

    today = current_app_date(now)
    days_ahead = 4 - today.weekday()
    if days_ahead > 0:
        days_ahead -= 7
    return today + timedelta(days=days_ahead)
