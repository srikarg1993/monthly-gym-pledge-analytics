import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

from data.metrics import (
    fastest_winner_date,
    frontload_vs_cram,
    lazy_logger_score,
    longest_streak,
    month_bounds,
    month_leaderboard,
)


def _df_for_month():
    return pd.DataFrame(
        {
            "name": ["Ann", "Ann", "Ann", "Bob", "Bob"],
            "workout_date": [
                date(2024, 1, 1),
                date(2024, 1, 1),
                date(2024, 1, 2),
                date(2024, 1, 1),
                date(2024, 1, 3),
            ],
            "burnt_250": [True, True, False, True, True],
            "month": ["2024-01"] * 5,
        }
    )


def test_month_leaderboard_counts_and_ordering():
    df = _df_for_month()
    out = month_leaderboard(df, "2024-01", cutoff=2, all_users=["Ann", "Bob", "Cara"])

    assert list(out["name"]) == ["Bob", "Ann", "Cara"]

    ann = out[out["name"] == "Ann"].iloc[0]
    bob = out[out["name"] == "Bob"].iloc[0]
    cara = out[out["name"] == "Cara"].iloc[0]

    assert ann["workout_days"] == 2
    assert ann["qualifying_days"] == 1
    assert ann["workouts_left"] == 1
    assert bool(ann["is_winner"]) is False
    assert ann["progress"] == 0.5

    assert bob["workout_days"] == 2
    assert bob["qualifying_days"] == 2
    assert bob["workouts_left"] == 0
    assert bool(bob["is_winner"]) is True
    assert bob["progress"] == 1.0

    assert cara["workout_days"] == 0
    assert cara["qualifying_days"] == 0
    assert cara["workouts_left"] == 2
    assert bool(cara["is_winner"]) is False
    assert cara["progress"] == 0.0


def test_longest_streak():
    assert longest_streak([]) == 0
    assert longest_streak([date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 4)]) == 2


def test_fastest_winner_date():
    df = _df_for_month()
    df_month = df[df["month"] == "2024-01"].copy()
    assert fastest_winner_date(df_month, "Bob", cutoff=2) == date(2024, 1, 3)
    assert fastest_winner_date(df_month, "Ann", cutoff=2) is None


def test_lazy_logger_score():
    df = pd.DataFrame(
        {
            "name": ["Ann", "Ann", "Bob"],
            "log_delay_days": [1, 3, 2],
            "workout_date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 1)],
            "timestamp": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-05"), pd.Timestamp("2024-01-03")],
        }
    )
    out = lazy_logger_score(df)
    assert list(out["name"]) == ["Ann", "Bob"]
    assert out.iloc[0]["avg_log_delay_days"] == 2.0

    empty = pd.DataFrame(columns=["name", "log_delay_days", "workout_date", "timestamp"])
    assert lazy_logger_score(empty) is None


def test_frontload_vs_cram():
    df = pd.DataFrame(
        {
            "name": ["Ann", "Ann", "Ann", "Ann", "Bob", "Bob", "Bob", "Bob", "Cara", "Cara"],
            "workout_date": [
                date(2024, 1, 1),
                date(2024, 1, 2),
                date(2024, 1, 3),
                date(2024, 1, 4),
                date(2024, 1, 20),
                date(2024, 1, 21),
                date(2024, 1, 22),
                date(2024, 1, 23),
                date(2024, 1, 10),
                date(2024, 1, 20),
            ],
            "burnt_250": [True] * 10,
            "month": ["2024-01"] * 10,
        }
    )
    out = frontload_vs_cram(df)
    styles = dict(zip(out["name"], out["style"]))
    assert styles["Ann"] == "Front-loader"
    assert styles["Bob"] == "Crammer"
    assert styles["Cara"] == "Balanced"


def test_month_bounds():
    start, end = month_bounds("2024-02")
    assert start == date(2024, 2, 1)
    assert end == date(2024, 2, 29)
