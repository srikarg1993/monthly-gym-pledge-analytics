from __future__ import annotations

from datetime import date, datetime
import os

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - fallback for older runtimes
    ZoneInfo = None


APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Chicago")


def _tzinfo():
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(APP_TIMEZONE)
    except Exception:
        return None


def now_app() -> datetime:
    tz = _tzinfo()
    if tz is None:
        return datetime.now()
    return datetime.now(tz)


def today_app() -> date:
    return now_app().date()


def current_month_str() -> str:
    t = today_app()
    return f"{t.year:04d}-{t.month:02d}"


def month_label(month_str: str | None = None) -> str:
    if month_str:
        try:
            dt = datetime.strptime(month_str, "%Y-%m")
            return dt.strftime("%b %Y")
        except Exception:
            pass
    return now_app().strftime("%b %Y")
