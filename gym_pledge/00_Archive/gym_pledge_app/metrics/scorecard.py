from __future__ import annotations

from datetime import date
import pandas as pd
from .dates import month_bounds


def longest_streak(dates) -> int:
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


def frontload_vs_cram(df_month: pd.DataFrame) -> pd.DataFrame:
    if df_month.empty:
        return pd.DataFrame()

    start, end = month_bounds(df_month["month"].iloc[0])
    mid = start + (end - start) / 2
    mid = date(mid.year, mid.month, int(mid.day))

    d = df_month[df_month["burnt_250"]].copy()

    def split_counts(x):
        days = sorted(set(x["workout_date"].dropna().tolist()))
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

    out = d.groupby("name").apply(split_counts).reset_index()
    return out.sort_values(["style", "first_half"], ascending=[True, False])
