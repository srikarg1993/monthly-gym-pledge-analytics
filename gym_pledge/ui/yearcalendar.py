"""Year calendar UI rendering helper."""

import calendar
from datetime import datetime

import pandas as pd
import streamlit as st

from app_time import today_app


def _name_col(df: pd.DataFrame) -> str:
    return "name" if df is not None and "name" in df.columns else "Name"


def _year_from_month_str(month_str: str | None) -> int:
    if month_str:
        try:
            return int(str(month_str).split("-")[0])
        except Exception:
            pass
    return today_app().year


def _status_by_day(df_month: pd.DataFrame, name: str, name_col: str) -> dict[int, str]:
    day_status: dict[int, str] = {}
    if df_month is None or df_month.empty:
        return day_status

    if name_col not in df_month.columns:
        return day_status

    person = df_month[df_month[name_col] == name]
    if person.empty:
        return day_status

    for _, row in person.iterrows():
        workout_date = row.get("workout_date")
        if pd.isna(workout_date):
            continue
        day = int(workout_date.day)
        if bool(row.get("burnt_250", False)):
            day_status[day] = "qualifying"
        else:
            day_status.setdefault(day, "regular")
    return day_status


def _calendar_html(*, year: int, month: int, status_by_day: dict[int, str], today, mini: bool = False) -> str:
    last_day_in_month = calendar.monthrange(year, month)[1]
    if (year, month) < (today.year, today.month):
        last_day_for_dots = last_day_in_month
    elif (year, month) > (today.year, today.month):
        last_day_for_dots = 0
    else:
        last_day_for_dots = today.day

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)

    calendar_class = "calendar calendar-mini" if mini else "calendar"
    parts = [f"<div class='{calendar_class}'><div class='calendar-grid'>"]

    for wd in weekdays:
        parts.append(f"<div class='cal-head'>{wd}</div>")

    for week in weeks:
        for day in week:
            if day == 0:
                parts.append("<div class='cal-cell cal-empty'></div>")
                continue

            status = status_by_day.get(day, "none")
            if status == "none" and day > last_day_for_dots:
                status = "future"
            day_class = "cal-day"
            dot_class = "cal-dot cal-dot-none"
            if status == "qualifying":
                day_class += " cal-day-qualifying"
                dot_class = "cal-dot cal-dot-hidden"
            elif status == "regular":
                day_class += " cal-day-regular"
                dot_class = "cal-dot cal-dot-hidden"
            elif status == "future":
                day_class += " cal-day-future"
                dot_class = "cal-dot cal-dot-hidden"

            parts.append(
                f"<div class='cal-cell'>"
                f"<div class='{day_class}'>{day}</div>"
                f"<div class='{dot_class}'></div>"
                f"</div>"
            )

    parts.append("</div></div>")
    return "".join(parts)


def _render_year_calendar(*, df_year: pd.DataFrame, name: str, year: int, name_col: str) -> None:
    today = today_app()
    parts = ["<div class='calendar-year'>"]

    for month in range(1, 13):
        month_str = f"{year:04d}-{month:02d}"
        if df_year is None or df_year.empty or "month" not in df_year.columns:
            month_df = pd.DataFrame(columns=df_year.columns if df_year is not None else [])
        else:
            month_df = df_year[df_year["month"] == month_str].copy()
        status_by_day = _status_by_day(month_df, name, name_col)
        month_label = datetime(year, month, 1).strftime("%b")

        parts.append("<div class='calendar-month'>")
        parts.append(f"<div class='calendar-month-title'>{month_label}</div>")
        parts.append(_calendar_html(year=year, month=month, status_by_day=status_by_day, today=today, mini=True))
        parts.append("</div>")

    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render(*, df: pd.DataFrame, month_selected: str) -> None:
    year = _year_from_month_str(month_selected)
    st.subheader(f"{year} Fitness Yearbook")
    # st.markdown("<div class='small-muted'>All 12 months - per-person view</div>", unsafe_allow_html=True)

    name_col = _name_col(df)
    df_year = df.copy() if df is not None else pd.DataFrame()
    if df_year is not None and not df_year.empty and "workout_date" in df_year.columns:
        dates = pd.to_datetime(df_year["workout_date"], errors="coerce")
        df_year = df_year[(df_year["workout_date"].notna()) & (dates.dt.year == year)].copy()

    people_source = df_year if df_year is not None and not df_year.empty else df
    if people_source is None or people_source.empty or name_col not in people_source.columns:
        st.caption(f"No participants found for {year}.")
        return

    people = sorted(people_source[name_col].dropna().unique().tolist())
    who = st.selectbox("Select person", people, key="year_calendar_person")

    st.markdown(
        """
        <div class="calendar-legend">
          <span class="legend-item"><span class="legend-swatch legend-qualifying"></span>Qualifying</span>
          <span class="legend-item"><span class="legend-swatch legend-regular"></span>Workout</span>
          <span class="legend-item"><span class="legend-dot legend-missed"></span>Missed day</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _render_year_calendar(df_year=df_year, name=who, year=year, name_col=name_col)
