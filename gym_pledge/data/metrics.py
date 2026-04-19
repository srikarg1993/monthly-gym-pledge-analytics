"""Metric computations for the Monthly Gym Pledge.

Contains leaderboard and per-person convenience functions used by the
dashboard UI.
"""

import calendar
from datetime import date

import pandas as pd


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
    out["rank"] = (
        out["qualifying_days"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )

    # Order leaderboard by qualifying workouts (desc) then alphabetically by name (asc)
    out = out.sort_values(
        ["qualifying_days", "name"],
        ascending=[False, True],
    ).reset_index(drop=True)

    return out


def longest_streak(dates):
    if not dates:
        return 0
    ds = sorted(set(dates))
    best = cur = 1
    for i in range(1, len(ds)):
        if (ds[i] - ds[i - 1]).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def fastest_winner_date(df_month: pd.DataFrame, name: str, cutoff: int):
    d = df_month[(df_month["name"] == name) & (df_month["burnt_250"])].copy()
    if d.empty:
        return None
    days = sorted(set(d["workout_date"].dropna().tolist()))
    if len(days) < cutoff:
        return None
    return days[cutoff - 1]


def lazy_logger_score(df_month: pd.DataFrame):
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


def frontload_vs_cram(df_month: pd.DataFrame):
    if df_month.empty:
        return pd.DataFrame()
    start, end = month_bounds(df_month["month"].iloc[0])
    mid = start + (end - start) / 2
    mid = date(mid.year, mid.month, int(mid.day))

    qual = df_month[df_month["burnt_250"]].copy()
    all_names = sorted(df_month["name"].dropna().unique().tolist())

    def split_counts(workout_dates):
        days = sorted(set(workout_dates.dropna().tolist()))
        first = sum(1 for dd in days if dd <= mid)
        second = sum(1 for dd in days if dd > mid)
        total = first + second
        if total == 0:
            style = "No qualifying"
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


def month_bounds(month_str: str):
    y, m = map(int, month_str.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last_day)
