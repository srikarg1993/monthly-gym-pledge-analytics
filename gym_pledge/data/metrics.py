"""Metric computations for the Monthly Gym Pledge.

Contains leaderboard and per-person convenience functions used by the
dashboard UI.
"""

import calendar
from collections.abc import Iterable
from datetime import date

import pandas as pd

from app_time import today_app


def month_leaderboard(df: pd.DataFrame, month_str: str, cutoff: int, all_users=None) -> pd.DataFrame:
    d = df[(df["month"] == month_str) & (df["workout_date"].notna())].copy()

    any_days = d.groupby("name")["workout_date"].nunique().rename("workout_days").reset_index()
    qual_days = d[d["burnt_250"]].groupby("name")["workout_date"].nunique().rename("qualifying_days").reset_index()

    if "calories_burned" in d.columns:
        cal_sum = d.groupby("name")["calories_burned"].sum().rename("total_calories").reset_index()
    else:
        cal_sum = pd.DataFrame({"name": d["name"].unique(), "total_calories": 0})

    out = any_days.merge(qual_days, on="name", how="left").merge(cal_sum, on="name", how="left")
    out["qualifying_days"] = out["qualifying_days"].fillna(0).astype(int)
    out["workout_days"] = out["workout_days"].fillna(0).astype(int)
    out["total_calories"] = out["total_calories"].fillna(0).astype(int)

    if all_users is not None:
        all_users_df = pd.DataFrame({"name": list(all_users)})
        out = all_users_df.merge(out, on="name", how="left").fillna(0)
        out["qualifying_days"] = out["qualifying_days"].astype(int)
        out["workout_days"] = out["workout_days"].astype(int)
        out["total_calories"] = out["total_calories"].astype(int)

    out["workouts_left"] = (cutoff - out["qualifying_days"]).clip(lower=0)
    out["is_winner"] = out["qualifying_days"] >= cutoff
    out["progress"] = (out["qualifying_days"] / max(cutoff, 1)).clip(0, 1)
    out["rank"] = out["qualifying_days"].rank(method="dense", ascending=False).astype(int)

    # Order leaderboard by qualifying workouts (desc) then alphabetically by name (asc)
    out = out.sort_values(
        ["qualifying_days", "name"],
        ascending=[False, True],
    ).reset_index(drop=True)

    return out


def longest_streak(dates: Iterable[date]) -> int:
    """Return the length of the longest run of consecutive calendar days.

    ``dates`` may contain duplicates and is treated as a set. Returns ``0``
    when the input is empty.
    """
    ds = sorted({d for d in dates if d is not None})
    if not ds:
        return 0
    best = cur = 1
    for i in range(1, len(ds)):
        if (ds[i] - ds[i - 1]).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def fastest_winner_date(df_month: pd.DataFrame, name: str, cutoff: int) -> date | None:
    d = df_month[(df_month["name"] == name) & (df_month["burnt_250"])].copy()
    if d.empty:
        return None
    days = sorted(set(d["workout_date"].dropna().tolist()))
    if len(days) < cutoff:
        return None
    return days[cutoff - 1]


def lazy_logger_score(df_month: pd.DataFrame) -> pd.DataFrame | None:
    d = df_month.dropna(subset=["workout_date", "timestamp"]).copy()
    if d.empty:
        return None
    agg = (
        d.groupby("name")["log_delay_days"]
        .mean()
        .rename("avg_log_delay_days")
        .reset_index()
        .sort_values("avg_log_delay_days", ascending=False)
    )
    return agg


def frontload_vs_cram(df_month: pd.DataFrame) -> pd.DataFrame:
    if df_month.empty:
        return pd.DataFrame()
    start, end = month_bounds(df_month["month"].iloc[0])
    mid = start + (end - start) / 2
    mid = date(mid.year, mid.month, int(mid.day))

    # Defense in depth: future-dated rows should already have been dropped in
    # data.source.clean, but the second-half logic below assumes today's date,
    # so we still gate on `today` rather than trust the input.
    today = today_app()
    qual = df_month[df_month["burnt_250"]].copy()
    all_names = sorted(df_month["name"].dropna().unique().tolist())

    # Once the month is current and we're still in the first half, the second
    # half hasn't started yet by definition — calling anyone "Balanced" or
    # "Crammer" mid-first-half is meaningless (e.g. first=1, second=0 should
    # not be "Balanced"). Collapse to a simple Front-loader / No qualifying
    # split until the calendar mid-point passes.
    second_half_started = today > mid

    def split_counts(workout_dates):
        days = sorted(set(workout_dates.dropna().tolist()))
        first = sum(1 for dd in days if dd <= mid)
        second = sum(1 for dd in days if dd > mid)
        total = first + second
        if total == 0:
            style = "No qualifying"
        elif not second_half_started:
            # Second half hasn't begun; second is forced to 0 above.
            style = "Front-loader"
        elif first >= second + 3:
            style = "Front-loader"
        elif second >= first + 3:
            style = "Crammer"
        else:
            style = "Balanced"
        return pd.Series({"first_half": first, "second_half": second, "style": style})

    if qual.empty:
        out = pd.DataFrame(
            [{"name": n, "first_half": 0, "second_half": 0, "style": "No qualifying"} for n in all_names]
        )
    else:
        out = qual.groupby("name")["workout_date"].apply(split_counts).unstack().reset_index()
        missing = [n for n in all_names if n not in set(out["name"])]
        if missing:
            filler = pd.DataFrame(
                [{"name": n, "first_half": 0, "second_half": 0, "style": "No qualifying"} for n in missing]
            )
            out = pd.concat([out, filler], ignore_index=True)
    out["first_half"] = out["first_half"].astype(int)
    out["second_half"] = out["second_half"].astype(int)
    return out.sort_values(["style", "first_half"], ascending=[True, False]).reset_index(drop=True)


def month_bounds(month_str: str) -> tuple[date, date]:
    """Return ``(first_day, last_day)`` for a ``YYYY-MM`` string."""
    y, m = map(int, month_str.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last_day)
