"""Leaderboard UI rendering helpers.

Provides functions to render the live leaderboard and person-level
details used by the main `dashboard` app.
"""

import calendar

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


from app_time import month_label, today_app
from config.globals import WINNER_CUTOFF
from ui.common import render_donut_days_left


def _name_col(df):
    """Return the canonical name column."""
    return "name" if "name" in df.columns else "Name"


def _render_kpis(lb, name_col: str, month_str: str) -> None:
    winners = lb[lb["is_winner"]]
    total_people = int(lb[name_col].nunique())
    winner_count = int(winners[name_col].nunique())
    month_year = month_label(month_str)

    st.markdown(
        f"""
        <div class="kpiRow">
          <div class="kpi">
            <div class="label">Participants</div>
            <div class="value">{total_people}</div>
          </div>
          <div class="kpi">
            <div class="label">Winners</div>
            <div class="value">{winner_count}</div>
          </div>
          <div class="kpi">
            <div class="label">Current Month</div>
            <div class="value">{month_year}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def _render_leaderboard_rows(lb, *, name_col: str, max_workouts: int) -> None:
    st.markdown("<div class='leaderboard'>", unsafe_allow_html=True)

    for _, row in lb.iterrows():
        qdays = int(row.get("qualifying_days", 0))
        progress = int((qdays / max_workouts) * 100) if max_workouts else 0
        progress = max(0, min(progress, 100))

        winner_class = "winner" if bool(row.get("is_winner", False)) else ""
        rank = row.get("rank", "")
        name = row.get(name_col, "")

        st.markdown(
            f"""
            <div class="lb-row {winner_class}">
              <div class="lb-rank">#{rank}</div>
              <div class="lb-name">{name}</div>
              <div class="lb-workouts">{qdays} workouts</div>
              <div class="lb-bar-wrap">
                <div class="lb-bar" style="width:{progress}%"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _donut_days_left(completed: int, cutoff: int) -> None:
    remaining = max(cutoff - completed, 0)

    fig, ax = plt.subplots()
    ax.pie(
        [completed, remaining],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.2, edgecolor="none"),
    )

    ax.text(
        0,
        0.05,
        f"{remaining}",
        ha="center",
        va="center",
        fontsize=30,
        fontweight="800",
        color="#E4E6EB",
    )
    ax.text(
        0,
        -0.18,
        "days left",
        ha="center",
        va="center",
        fontsize=15,
        color="#A0A4B3",
    )
    ax.axis("equal")

    st.pyplot(fig, transparent=True)

    if remaining == 0:
        st.success("Winner locked 🏆")
    else:
        st.info("Keep going!")


def _month_year_from_str(month_str: str) -> tuple[int, int]:
    try:
        year_str, month_str = month_str.split("-")
        return int(year_str), int(month_str)
    except Exception:
        today = today_app()
        return today.year, today.month


def _status_by_day(df_month: pd.DataFrame, name: str) -> dict[int, str]:
    day_status: dict[int, str] = {}
    if df_month is None or df_month.empty:
        return day_status

    person = df_month[df_month["name"] == name]
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


def _render_workout_calendar(*, df_month: pd.DataFrame, name: str, month_str: str) -> None:
    st.markdown("#### Workout calendar")

    year, month = _month_year_from_str(month_str)
    today = today_app()
    last_day_in_month = calendar.monthrange(year, month)[1]
    if (year, month) < (today.year, today.month):
        last_day_for_dots = last_day_in_month
    elif (year, month) > (today.year, today.month):
        last_day_for_dots = 0
    else:
        last_day_for_dots = today.day
    status_by_day = _status_by_day(df_month, name)

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

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)

    parts = ["<div class='calendar'><div class='calendar-grid'>"]
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
    st.markdown("".join(parts), unsafe_allow_html=True)


def render(*, df, df_month, month_str: str) -> None:
    lb = df.copy()
    name_col = _name_col(lb)

    left, right = st.columns([1.9, 1.0], gap="large")

    # ---------------- LEFT: Leaderboard ----------------
    with left:
        st.subheader("Live Leaderboard")
        _render_kpis(lb, name_col, month_str)

        max_workouts = WINNER_CUTOFF  
        _render_leaderboard_rows(lb, name_col=name_col, max_workouts=max_workouts)

    # ---------------- RIGHT: Person detail ----------------
    with right:
        # st.subheader("Workouts left (by person)")

        people = sorted(lb[name_col].dropna().unique().tolist())
        if not people:
            st.warning("No participants found.")
            return

        who = st.selectbox("Select person", people)

        selected = lb[lb[name_col] == who]
        if selected.empty:
            st.warning("No data found for selected person.")
            return

        row = selected.iloc[0]
        qdays = int(row.get("qualifying_days", 0))
        # wdays = int(row.get("workout_days", 0))         # keep if you use it
        # workouts_left = int(row.get("workouts_left", 0)) # keep if you use it

        st.markdown(f"### {who}")
        st.markdown("<div class='small-muted'>This month</div>", unsafe_allow_html=True)

        fig, remaining = render_donut_days_left(completed=qdays, cutoff=WINNER_CUTOFF)
        st.pyplot(fig, transparent=True)

        _render_workout_calendar(df_month=df_month, name=who, month_str=month_str)
        st.markdown("<div class='calendar-spacer'></div>", unsafe_allow_html=True)

        if remaining == 0:
            st.success("Winner locked 🏆")
        else:
            st.info("Keep going!")
