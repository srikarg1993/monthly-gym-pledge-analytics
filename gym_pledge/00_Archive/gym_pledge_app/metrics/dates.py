from __future__ import annotations

import calendar
from datetime import date
from typing import Tuple


def current_month_str(today: date | None = None) -> str:
    t = today or date.today()
    return f"{t.year:04d}-{t.month:02d}"


def month_bounds(month_str: str) -> Tuple[date, date]:
    y, m = map(int, month_str.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last_day)
