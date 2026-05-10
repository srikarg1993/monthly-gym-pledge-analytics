"""Timezone-aware ``now`` / ``today`` for the app.

Centralizes timezone handling so business logic never calls
``datetime.now()`` / ``date.today()`` directly. The ``APP_TIMEZONE``
environment variable selects the IANA zone name; the default
``America/Chicago`` matches where the participant group lives. Override
in deployment via Streamlit Cloud secrets / environment variables.
See [ADR 0004](../docs/adr/0004-timezone-via-app-time.md).
"""

from __future__ import annotations

import os
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # pragma: no cover - fallback for older runtimes
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception  # type: ignore[assignment,misc]


# Default tracks where the pledge group physically lives. Override per
# deployment via the ``APP_TIMEZONE`` environment variable.
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Chicago")


def _tzinfo() -> ZoneInfo | None:
    """Return a `ZoneInfo` for `APP_TIMEZONE`, or ``None`` on bad config.

    On bad config we deliberately fall back to system local time rather
    than raising — a misconfigured deployment env var should not black
    out the whole dashboard. The caller logs nothing because
    `app_time.now_app()` is called many times per render; warn at
    deployment time instead by validating the env var.
    """
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(APP_TIMEZONE)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def now_app() -> datetime:
    """Return the current `datetime` in the configured app timezone."""
    tz = _tzinfo()
    if tz is None:
        return datetime.now()
    return datetime.now(tz)


def today_app() -> date:
    """Return the current calendar date in the configured app timezone."""
    return now_app().date()


def current_month_str() -> str:
    """Return ``YYYY-MM`` for the current month in the app timezone."""
    t = today_app()
    return f"{t.year:04d}-{t.month:02d}"


def month_label(month_str: str | None = None) -> str:
    """Format a ``YYYY-MM`` string as ``Mon YYYY`` for display.

    Falls back to the current month when input is missing or malformed.
    """
    if month_str:
        try:
            dt = datetime.strptime(month_str, "%Y-%m")
            return dt.strftime("%b %Y")
        except ValueError:
            pass
    return now_app().strftime("%b %Y")
