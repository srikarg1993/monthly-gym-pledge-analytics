#libraries
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass
from typing import Set


@dataclass(frozen=True)
class SheetSchema:
    timestamp: str = "Timestamp"
    name: str = "You are?"
    workout_date: str = "Workout date"
    burnt_250: str = "Burnt >= 250 calories?"


def normalize_bool(x) -> bool:
    if pd.isna(x):
        return False
    s = str(x).strip().lower()
    return s in {"yes", "true", "1", "y", "t"}


def clean_sheet(
    df: pd.DataFrame,
    *,
    schema: SheetSchema = SheetSchema(),
    dedupe: bool = True,
) -> pd.DataFrame:
    """Clean raw sheet data into a typed analytics-ready dataframe."""
    df = df.copy()

    expected: Set[str] = {schema.timestamp, schema.name, schema.workout_date, schema.burnt_250}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found columns: {list(df.columns)}")

    df = df.rename(
        columns={
            schema.timestamp: "timestamp",
            schema.name: "name_raw",
            schema.workout_date: "workout_date_raw",
            schema.burnt_250: "burnt_250_raw",
        }
    )

    df["name"] = df["name_raw"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["timestamp_date"] = df["timestamp"].dt.date

    df["workout_date"] = pd.to_datetime(df["workout_date_raw"], errors="coerce").dt.date
    df["burnt_250"] = df["burnt_250_raw"].apply(normalize_bool)

    if dedupe:
        df = (
            df.sort_values("timestamp", ascending=True)
            .drop_duplicates(subset=["name", "workout_date"], keep="last")
            .reset_index(drop=True)
        )

    df["any_workout"] = df["workout_date"].notna()
    df["workout_dt"] = pd.to_datetime(df["workout_date"], errors="coerce")
    df["month"] = df["workout_dt"].dt.to_period("M").astype(str)
    df["dow"] = df["workout_dt"].dt.day_name()
    df["dom"] = df["workout_dt"].dt.day

    df["log_delay_days"] = (
        pd.to_datetime(df["timestamp_date"], errors="coerce")
        - pd.to_datetime(df["workout_date"], errors="coerce")
    ).dt.days

    return df
