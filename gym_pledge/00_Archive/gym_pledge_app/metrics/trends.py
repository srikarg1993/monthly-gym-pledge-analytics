from __future__ import annotations

import pandas as pd


def build_month_over_month(df: pd.DataFrame, winner_cutoff: int) -> pd.DataFrame:
    participants = df[df["any_workout"]].groupby("month")["name"].nunique().reset_index(name="Participants")
    total_workouts = df[df["any_workout"]].groupby("month")["workout_date"].nunique().reset_index(
        name="Total unique workout days"
    )

    qual = (
        df[df["burnt_250"]]
        .groupby(["month", "name"])["workout_date"]
        .nunique()
        .reset_index(name="qualifying_days")
    )
    avg_qual = qual.groupby("month")["qualifying_days"].mean().reset_index(name="Avg qualifying days / person")

    winners = qual.copy()
    winners["is_winner"] = winners["qualifying_days"] >= winner_cutoff
    winner_count = winners[winners["is_winner"]].groupby("month")["name"].nunique().reset_index(name="Winners")

    mom = (
        participants.merge(total_workouts, on="month", how="left")
        .merge(avg_qual, on="month", how="left")
        .merge(winner_count, on="month", how="left")
        .fillna({"Winners": 0, "Avg qualifying days / person": 0})
        .sort_values("month")
        .reset_index(drop=True)
    )
    return mom
