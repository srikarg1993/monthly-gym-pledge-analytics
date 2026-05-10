"""Month-over-month trends page: leaderboard comparisons and engagement metrics."""

from __future__ import annotations

import math
from datetime import datetime

import pandas as pd
import streamlit as st

from app_time import current_month_str
from config.globals import winner_cutoff_for_month
from data.metrics import month_leaderboard
from data.source import get_users
from ui.common import render_styled_table


def _month_label(month_str: str) -> str:
    try:
        return datetime.strptime(month_str, "%Y-%m").strftime("%b %Y")
    except Exception:
        return month_str


def _prev_month(month_str: str) -> str:
    try:
        return (pd.Period(month_str, freq="M") - 1).strftime("%Y-%m")
    except Exception:
        return month_str


def _format_percent(value: float | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value * 100:.{decimals}f}%"


def _format_number(value: float | int | None, decimals: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    if decimals == 0:
        return f"{int(round(value)):,}"
    return f"{value:.{decimals}f}"


def _build_per_person(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["month", "name", "workout_days", "qualifying_days"])

    any_workout = df[df["any_workout"]]
    if any_workout.empty:
        return pd.DataFrame(columns=["month", "name", "workout_days", "qualifying_days"])

    workouts = any_workout.groupby(["month", "name"])["workout_date"].nunique().reset_index(name="workout_days")
    qualifying = (
        any_workout[any_workout["burnt_250"]]
        .groupby(["month", "name"])["workout_date"]
        .nunique()
        .reset_index(name="qualifying_days")
    )

    per_person = workouts.merge(qualifying, on=["month", "name"], how="left")
    per_person["qualifying_days"] = per_person["qualifying_days"].fillna(0).astype(int)
    per_person["workout_days"] = per_person["workout_days"].fillna(0).astype(int)
    return per_person


def _build_leaderboard_comparison_table(df: pd.DataFrame, last_month: str, current_month: str) -> pd.DataFrame:
    prev_label = "Previous"
    current_label = "Current"
    users_last = get_users(last_month)
    users_current = get_users(current_month)

    lb_last = month_leaderboard(df, last_month, winner_cutoff_for_month(last_month), users_last.users or None)
    lb_current = month_leaderboard(
        df, current_month, winner_cutoff_for_month(current_month), users_current.users or None
    )

    names = sorted(set(lb_last.get("name", [])) | set(lb_current.get("name", [])))
    if not names:
        return pd.DataFrame(columns=["Name", prev_label, current_label])

    last_rank = lb_last.set_index("name")["rank"] if "name" in lb_last.columns else pd.Series(dtype=float)
    current_rank = lb_current.set_index("name")["rank"] if "name" in lb_current.columns else pd.Series(dtype=float)

    comparison = pd.DataFrame({"Name": names})
    comparison[prev_label] = comparison["Name"].map(last_rank)
    comparison[current_label] = comparison["Name"].map(current_rank)

    comparison[prev_label] = comparison[prev_label].apply(_format_number)
    comparison[current_label] = comparison[current_label].apply(_format_number)
    return comparison.sort_values("Name").reset_index(drop=True)


def _build_participation_table(per_person: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    if per_person.empty:
        return pd.DataFrame(
            columns=[
                "Month",
                "Participants",
                "New participants",
                "Winners",
                "Returning participants",
                "Retention rate",
                "Reactivation count",
            ]
        )

    with_cutoff = per_person.copy()
    with_cutoff["winner_cutoff"] = with_cutoff["month"].map(winner_cutoff_for_month).astype(int)
    winners_by_month = (
        with_cutoff[with_cutoff["qualifying_days"] >= with_cutoff["winner_cutoff"]].groupby("month")["name"].nunique()
    )
    first_month_by_name = per_person.groupby("name")["month"].min()

    participants_by_month: dict[str, set[str]] = {}
    for month_str, group in per_person.groupby("month"):
        participants_by_month[month_str] = set(group["name"].tolist())

    rows: list[dict[str, object]] = []
    prev_participants: set[str] | None = None

    for month_str in months:
        current_participants = participants_by_month.get(month_str, set())
        total_participants = len(current_participants)
        new_participants = int((first_month_by_name == month_str).sum())
        winners = int(winners_by_month.get(month_str, 0))
        returning = total_participants - new_participants

        if prev_participants is None:
            retention_rate = None
            reactivation = 0
        else:
            prev_count = len(prev_participants)
            retained = len(current_participants & prev_participants)
            retention_rate = retained / prev_count if prev_count else 0
            reactivation = len(current_participants - prev_participants) - new_participants
            reactivation = max(reactivation, 0)

        rows.append(
            {
                "Month": _month_label(month_str),
                "Participants": total_participants,
                "New participants": new_participants,
                "Winners": winners,
                "Returning participants": returning,
                "Retention rate": retention_rate,
                "Reactivation count": reactivation,
            }
        )
        prev_participants = current_participants

    out = pd.DataFrame(rows)
    out["Participants"] = out["Participants"].apply(_format_number)
    out["New participants"] = out["New participants"].apply(_format_number)
    out["Winners"] = out["Winners"].apply(_format_number)
    out["Returning participants"] = out["Returning participants"].apply(_format_number)
    out["Retention rate"] = out["Retention rate"].apply(_format_percent)
    out["Reactivation count"] = out["Reactivation count"].apply(_format_number)
    return out


def _build_avg_qual_table(per_person: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    if per_person.empty:
        return pd.DataFrame(columns=["Month", "Avg qualifying days per participant"])

    avg_qual = per_person.groupby("month")["qualifying_days"].mean().reindex(months).fillna(0)
    rows = [
        {
            "Month": _month_label(month_str),
            "Avg qualifying days per participant": _format_number(avg_qual.loc[month_str], decimals=2),
        }
        for month_str in months
    ]
    return pd.DataFrame(rows)


def _share_of(values: pd.Series, count: int, *, top: bool = True) -> float:
    if values.empty:
        return 0.0
    total = values.sum()
    if total <= 0:
        return 0.0
    ordered = values.sort_values(ascending=not top)
    return ordered.head(count).sum() / total


def _build_engagement_table(per_person: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    if per_person.empty:
        return pd.DataFrame(
            columns=[
                "Month",
                "Top 10% share",
                "Top 5 contributors share",
                "Bottom 50% share",
            ]
        )

    rows: list[dict[str, object]] = []
    for month_str in months:
        month_values = per_person.loc[per_person["month"] == month_str, "workout_days"]
        total_people = len(month_values)
        top_10_count = max(1, math.ceil(total_people * 0.10))
        top_5_count = max(1, min(5, total_people))
        bottom_50_count = max(1, math.ceil(total_people * 0.50))

        rows.append(
            {
                "Month": _month_label(month_str),
                "Top 10% share": _format_percent(_share_of(month_values, top_10_count, top=True)),
                "Top 5 contributors share": _format_percent(_share_of(month_values, top_5_count, top=True)),
                "Bottom 50% share": _format_percent(_share_of(month_values, bottom_50_count, top=False)),
            }
        )

    return pd.DataFrame(rows)


def render(*, df) -> None:
    per_person = _build_per_person(df)
    months = sorted(per_person["month"].dropna().unique().tolist())
    if not months:
        st.warning("No workouts found yet.")
        return

    current_month = current_month_str()
    last_month = _prev_month(current_month)

    with st.container(key="leaderboard_comparison"):
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:12px; margin: 6px 0 12px;">
              <div style="font-size:1.25rem; font-weight:800;">Leaderboard Comparison</div>
              <div class="badge"><span class="dot"></span>{_month_label(last_month)} vs {_month_label(current_month)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        comparison = _build_leaderboard_comparison_table(df, last_month, current_month)
        render_styled_table(comparison)

    st.markdown("<hr>", unsafe_allow_html=True)

    with st.container(key="participation_table"):
        st.markdown("#### Participation")
        participation = _build_participation_table(per_person, months)
        render_styled_table(participation)

    st.markdown("<hr>", unsafe_allow_html=True)

    with st.container(key="avg_qualifying_table"):
        st.markdown("#### Avg qualifying days per participant")
        avg_qual = _build_avg_qual_table(per_person, months)
        render_styled_table(avg_qual)

    st.markdown("<hr>", unsafe_allow_html=True)

    with st.container(key="engagement_concentration_table"):
        st.markdown("#### Engagement concentration")
        engagement = _build_engagement_table(per_person, months)
        render_styled_table(engagement)
