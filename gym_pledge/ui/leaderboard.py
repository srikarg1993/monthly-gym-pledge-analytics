"""Leaderboard UI rendering helpers.

Provides functions to render the live leaderboard and person-level
details used by the main `dashboard` app.
"""

import calendar
from html import escape

import pandas as pd
import streamlit as st

from app_time import month_label, today_app


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


def _safe_key(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


def _progress_ratio(current: int, total: int) -> float:
    if total <= 0:
        return 0.0

    bounded_current = max(0, min(current, total))
    return bounded_current / total


def _render_leaderboard_rows(lb, *, name_col: str, cutoff: int, active_name: str) -> str:
    if lb.empty:
        st.info("No leaderboard entries for this month yet.")
        return active_name

    ranked = lb.copy()
    if "rank" not in ranked.columns:
        ranked["rank"] = (
            ranked["qualifying_days"].rank(method="dense", ascending=False).astype(int)
        )

    ranked = ranked.sort_values(["rank", "qualifying_days", name_col], ascending=[True, False, True])

    card_meta: list[tuple[str, bool, str, float]] = []
    for rank, group in ranked.groupby("rank", sort=True):
        rank_value = int(rank)
        people_count = int(len(group))
        participant_text = "participant" if people_count == 1 else "participants"

        with st.container(key=f"lb_rank_{rank_value}"):
            st.markdown(
                f"<div class='lb-rank-header'>"
                f"<span>Rank #{rank_value}</span>"
                f"<span>{people_count} {participant_text}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            rows = group.to_dict("records")
            for row_start in range(0, len(rows), 3):
                cols = st.columns(3, gap="small")
                for col_idx, row in enumerate(rows[row_start : row_start + 3]):
                    col = cols[col_idx]
                    with col:
                        raw_name = str(row.get(name_col, ""))
                        qdays = int(row.get("qualifying_days", 0))
                        winner = bool(row.get("is_winner", False))
                        progress = _progress_ratio(qdays, cutoff)
                        key = f"lb_pick_{rank_value}_{row_start + col_idx}_{_safe_key(raw_name)}"
                        label = f"**{escape(raw_name)}**  \n{qdays}/{cutoff}"

                        if st.button(label, key=key, use_container_width=True):
                            active_name = raw_name

                        card_meta.append((key, winner, raw_name, progress))

    style_rules: list[str] = []
    for key, winner, raw_name, progress in card_meta:
        selector = f"div[class*='st-key-{key}'] button"
        style_rules.append(f"{selector}{{--lb-progress:{progress:.4f};}}")
        if winner and raw_name == active_name:
            style_rules.append(
                f"{selector}{{border-color:rgba(16,185,129,0.85)!important;"
                f"box-shadow:0 0 0 1px rgba(16,185,129,0.4) inset!important;"
                f"background:rgba(16,185,129,0.14)!important;"
                f"--lb-progress-fill:linear-gradient(90deg,rgba(16,185,129,0.95),rgba(52,211,153,0.95));}}"
            )
        elif winner:
            style_rules.append(
                f"{selector}{{border-color:rgba(16,185,129,0.65)!important;"
                f"background:rgba(16,185,129,0.14)!important;"
                f"--lb-progress-fill:linear-gradient(90deg,rgba(16,185,129,0.95),rgba(52,211,153,0.95));}}"
            )
        elif raw_name == active_name:
            style_rules.append(
                f"{selector}{{border-color:rgba(99,102,241,0.8)!important;"
                f"box-shadow:0 0 0 1px rgba(99,102,241,0.35) inset!important;}}"
            )

    if style_rules:
        st.markdown(f"<style>{''.join(style_rules)}</style>", unsafe_allow_html=True)

    return active_name


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


def render(*, df, df_month, month_str: str, cutoff: int) -> None:
    lb = df.copy()
    name_col = _name_col(lb)
    people = sorted(lb[name_col].dropna().astype(str).unique().tolist())
    if not people:
        st.warning("No participants found.")
        return

    state_key = "leaderboard_active_person"
    if st.session_state.get(state_key) not in people:
        st.session_state[state_key] = people[0]
    active_person = str(st.session_state[state_key])

    left, right = st.columns([1.9, 1.0], gap="large")

    # ---------------- LEFT: Leaderboard ----------------
    with left:
        st.subheader("Live Leaderboard")
        _render_kpis(lb, name_col, month_str)
        st.caption("Click a participant card to view their workout calendar.")
        active_person = _render_leaderboard_rows(
            lb,
            name_col=name_col,
            cutoff=cutoff,
            active_name=active_person,
        )
        st.session_state[state_key] = active_person

    # ---------------- RIGHT: Person detail ----------------
    with right:
        selected = lb[lb[name_col].astype(str) == active_person]
        if selected.empty:
            st.warning("No data found for selected person.")
            return

        row = selected.iloc[0]
        qdays = int(row.get("qualifying_days", 0))
        remaining = max(cutoff - qdays, 0)

        st.markdown(f"### {active_person}")
        st.markdown(
            f"<div class='small-muted'>{qdays} out of {cutoff} workouts completed.</div>",
            unsafe_allow_html=True,
        )
        _render_workout_calendar(df_month=df_month, name=active_person, month_str=month_str)
        st.markdown("<div class='calendar-spacer'></div>", unsafe_allow_html=True)

        if remaining == 0:
            st.success("Winner locked")
        else:
            st.info("Keep going!")
