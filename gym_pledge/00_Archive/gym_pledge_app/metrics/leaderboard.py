from __future__ import annotations

import pandas as pd


def month_leaderboard(df: pd.DataFrame, month_str: str, cutoff: int) -> pd.DataFrame:
    d = df[(df["month"] == month_str) & (df["workout_date"].notna())].copy()

    any_days = d.groupby("name")["workout_date"].nunique().rename("workout_days").reset_index()
    qual_days = (
        d[d["burnt_250"]].groupby("name")["workout_date"].nunique().rename("qualifying_days").reset_index()
    )

    out = any_days.merge(qual_days, on="name", how="left")
    out["qualifying_days"] = out["qualifying_days"].fillna(0).astype(int)
    out["workout_days"] = out["workout_days"].fillna(0).astype(int)
    out["workouts_left"] = (cutoff - out["qualifying_days"]).clip(lower=0).astype(int)
    out["is_winner"] = out["qualifying_days"] >= cutoff
    out["progress"] = (out["qualifying_days"] / max(cutoff, 1)).clip(0, 1)

    out = out.sort_values(
        ["is_winner", "qualifying_days", "workout_days", "name"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)

    return out
