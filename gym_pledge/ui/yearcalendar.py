"""Year calendar UI rendering helper.

Replaces the previous ApexCharts CDN dependency (P1-12) with native
Altair charts so the page renders without an external script. Escapes
all dynamic names before HTML/SVG injection (P0-02). Splits the dense
single-page layout into tabs (P2-25) so mobile users aren't asked to
scroll past 12 calendar grids to find the chart they wanted.
"""

from __future__ import annotations

import calendar
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from app_time import today_app
from data.metrics import longest_streak
from ui.common import render_styled_table
from ui.escape import safe_html
from ui.theme import ALT_GRID, ALT_MUTED, ALT_PRIMARY, ALT_TEXT, GROUP_BRIGHT, WINNER_BRIGHT


def _name_col(df: pd.DataFrame) -> str:
    return "name" if df is not None and "name" in df.columns else "Name"


def _year_from_month_str(month_str: str | None) -> int:
    if month_str:
        try:
            return int(str(month_str).split("-")[0])
        except (ValueError, AttributeError, IndexError):
            return today_app().year
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
                f"<div class='cal-cell'><div class='{day_class}'>{day}</div><div class='{dot_class}'></div></div>"
            )

    parts.append("</div></div>")
    return "".join(parts)


def _year_stats_for_person(
    df_year: pd.DataFrame, name: str, name_col: str, year: int
) -> tuple[int, int, int, pd.DataFrame]:
    """Compute full-year stats for one person.

    Returns ``(workout_days, qualifying_days, longest_streak, monthly_df)``.
    """
    if df_year is None or df_year.empty or name_col not in df_year.columns:
        return 0, 0, 0, pd.DataFrame()

    person = df_year[df_year[name_col] == name]
    if person.empty:
        return 0, 0, 0, pd.DataFrame()

    workout_days = int(person["workout_date"].nunique())
    qual = person[person["burnt_250"]]
    qualifying_days = int(qual["workout_date"].nunique())
    streak = longest_streak(qual["workout_date"].dropna().tolist())

    monthly_rows = []
    if "month" in df_year.columns:
        for month in range(1, 13):
            month_str = f"{year:04d}-{month:02d}"
            m = person[person["month"] == month_str]
            w = int(m["workout_date"].nunique())
            q = int(m[m["burnt_250"]]["workout_date"].nunique())
            monthly_rows.append(
                {
                    "Month": datetime(year, month, 1).strftime("%b"),
                    "Workouts": w,
                    "Qualifying": q,
                }
            )
    monthly_df = pd.DataFrame(monthly_rows) if monthly_rows else pd.DataFrame()

    return workout_days, qualifying_days, streak, monthly_df


def _altair_monthly_chart(monthly_df: pd.DataFrame) -> alt.Chart:
    """Native Altair grouped bar chart for monthly Workouts / Qualifying.

    Replaces the prior ApexCharts CDN embed. No external network dep,
    no JS injection, native Altair tooltips and theming.
    """
    if monthly_df is None or monthly_df.empty:
        return alt.Chart(pd.DataFrame()).mark_bar()

    long = monthly_df.melt(id_vars="Month", var_name="Series", value_name="Count")
    month_order = monthly_df["Month"].tolist()
    series_order = ["Workouts", "Qualifying"]
    color_scale = alt.Scale(
        domain=series_order,
        range=[GROUP_BRIGHT, WINNER_BRIGHT],
    )

    bars = (
        alt.Chart(long)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("Month:N", sort=month_order, title=None, axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("Series:N", sort=series_order),
            y=alt.Y("Count:Q", title=None),
            color=alt.Color("Series:N", scale=color_scale, legend=alt.Legend(orient="top", title=None)),
            tooltip=[
                alt.Tooltip("Month:N"),
                alt.Tooltip("Series:N"),
                alt.Tooltip("Count:Q", format="d"),
            ],
        )
        .properties(height=280, background="#0B1220")
    )
    return (
        bars.configure_view(strokeOpacity=0, fill="#0B1220")
        .configure_axis(
            labelColor=ALT_MUTED,
            titleColor=ALT_TEXT,
            domainColor=ALT_GRID,
            gridColor=ALT_GRID,
            tickColor=ALT_GRID,
        )
        .configure_legend(labelColor=ALT_TEXT, titleColor=ALT_TEXT)
    )


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
        parts.append(f"<div class='calendar-month-title'>{safe_html(month_label)}</div>")
        parts.append(_calendar_html(year=year, month=month, status_by_day=status_by_day, today=today, mini=True))
        parts.append("</div>")

    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render(*, df: pd.DataFrame, month_selected: str) -> None:
    year = _year_from_month_str(month_selected)
    st.subheader(f"{year} Fitness Yearbook")

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

    workout_days, qualifying_days, streak, monthly_df = _year_stats_for_person(df_year, who, name_col, year)

    # Tab the dense single-page layout into Overview / Monthly / Calendar
    # so mobile users aren't asked to scroll past 12 mini-calendars to
    # see headline numbers (adversarial finding P2-25).
    overview_tab, breakdown_tab, calendar_tab = st.tabs(["Overview", "Monthly breakdown", "Calendar"])

    q_pct = (qualifying_days / workout_days * 100) if workout_days else 0

    with overview_tab:
        st.markdown("#### Full year stats")
        st.caption("Streak = longest run of consecutive qualifying days in the year (can span months).")
        stat_cols = st.columns(4, gap="small")
        stats = [
            ("Total workout days", f"{workout_days}"),
            ("Qualifying workouts", f"{qualifying_days}"),
            ("Q / W %", f"{q_pct:.1f}%"),
            ("Longest qualifying streak (across full year)", f"{streak} days"),
        ]
        for c, (label, value) in zip(stat_cols, stats, strict=False):
            with c:
                st.markdown(
                    f"""
                    <div style='background: rgba(255,255,255,0.02); padding:14px; border-radius:8px; text-align:center;'>
                      <div style='font-size:20px; font-weight:700; color:#fff;'>{safe_html(value)}</div>
                      <div style='font-size:12px; color:#9aa0ab; margin-top:6px;'>{safe_html(label)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with breakdown_tab:
        if not monthly_df.empty:
            st.markdown("#### Monthly breakdown")
            chart = _altair_monthly_chart(monthly_df)
            st.altair_chart(chart, use_container_width=True)
            with st.expander("View as table"):
                render_styled_table(monthly_df, max_rows=12)
        else:
            st.caption("No monthly data to display.")

    with calendar_tab:
        st.markdown(
            """
            <div class="calendar-legend">
              <span class="legend-item"><span class="legend-swatch legend-qualifying"></span>Qualifying</span>
              <span class="legend-item"><span class="legend-swatch legend-regular"></span>Workout</span>
              <span class="legend-item"><span class="legend-dot legend-missed"></span>No log</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _render_year_calendar(df_year=df_year, name=who, year=year, name_col=name_col)


# Avoid `ALT_PRIMARY` unused-import lint when the module is later split.
_ = ALT_PRIMARY
