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
            "calories_burned": [300, 300, 100, 400, 350],
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
    styles = dict(zip(out["name"], out["style"], strict=False))
    assert styles["Ann"] == "Front-loader"
    assert styles["Bob"] == "Crammer"
    assert styles["Cara"] == "Balanced"


def test_month_bounds():
    start, end = month_bounds("2024-02")
    assert start == date(2024, 2, 1)
    assert end == date(2024, 2, 29)


def test_month_leaderboard_total_calories():
    df = _df_for_month()
    out = month_leaderboard(df, "2024-01", cutoff=2, all_users=["Ann", "Bob", "Cara"])

    ann = out[out["name"] == "Ann"].iloc[0]
    bob = out[out["name"] == "Bob"].iloc[0]
    cara = out[out["name"] == "Cara"].iloc[0]

    assert ann["total_calories"] == 700  # 300 + 300 + 100
    assert bob["total_calories"] == 750  # 400 + 350
    assert cara["total_calories"] == 0


def test_month_leaderboard_without_calories_column():
    df = pd.DataFrame(
        {
            "name": ["Ann", "Bob"],
            "workout_date": [date(2024, 1, 1), date(2024, 1, 1)],
            "burnt_250": [True, True],
            "month": ["2024-01"] * 2,
        }
    )
    out = month_leaderboard(df, "2024-01", cutoff=1)
    assert "total_calories" in out.columns
    assert (out["total_calories"] == 0).all()


def test_frontload_vs_cram_includes_non_qualifying_users():
    df = pd.DataFrame(
        {
            "name": ["Ann", "Ann", "Bob"],
            "workout_date": [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 5)],
            "burnt_250": [True, True, False],
            "month": ["2024-01"] * 3,
        }
    )
    out = frontload_vs_cram(df)
    styles = dict(zip(out["name"], out["style"], strict=False))
    assert "Bob" in styles
    assert styles["Bob"] == "No qualifying"
    bob = out[out["name"] == "Bob"].iloc[0]
    assert int(bob["first_half"]) == 0
    assert int(bob["second_half"]) == 0


def test_frontload_vs_cram_all_non_qualifying():
    df = pd.DataFrame(
        {
            "name": ["Ann", "Bob"],
            "workout_date": [date(2024, 1, 2), date(2024, 1, 5)],
            "burnt_250": [False, False],
            "month": ["2024-01", "2024-01"],
        }
    )
    out = frontload_vs_cram(df)
    assert set(out["name"]) == {"Ann", "Bob"}
    assert set(out["style"]) == {"No qualifying"}


# ---------------------------------------------------------------------------
# Mutant-killing tests for month_leaderboard.
#
# Background: a 2026-05-09 mutmut pass on data/metrics.py reported 7 surviving
# mutations in month_leaderboard — changes to the source that the existing test
# suite did not detect. The three tests below close those gaps.
# ---------------------------------------------------------------------------


def test_month_leaderboard_excludes_other_months_and_nat_dates():
    """Filter must require BOTH month match AND non-NaT workout_date.

    Kills the mutation that flips `&` to `|` in the row filter, which would
    leak in rows from other months and rows with NaT workout dates.
    """
    df = pd.DataFrame(
        {
            "name": ["Ann", "Ann", "Bob", "Cara"],
            "workout_date": [
                date(2024, 1, 1),
                date(2024, 2, 1),  # wrong month, should be excluded
                pd.NaT,  # NaT, should be excluded
                date(2024, 1, 5),
            ],
            "burnt_250": [True, True, True, True],
            "month": ["2024-01", "2024-02", "2024-01", "2024-01"],
            "calories_burned": [300, 300, 300, 300],
        }
    )
    out = month_leaderboard(df, "2024-01", cutoff=2)
    # Bob (NaT) and Ann's Feb row are dropped, so only Ann + Cara appear,
    # each with exactly one workout day.
    assert set(out["name"]) == {"Ann", "Cara"}
    assert int(out[out["name"] == "Ann"].iloc[0]["workout_days"]) == 1
    assert int(out[out["name"] == "Cara"].iloc[0]["workout_days"]) == 1


def test_month_leaderboard_user_with_no_qualifying_no_all_users():
    """A user with workouts but zero qualifying days reports 0, not 1.

    Kills the mutation that changes `fillna(0)` to `fillna(1)` on
    qualifying_days. Without `all_users`, there is no second fillna pass
    to mask the bug, so the value flows straight into workouts_left.
    """
    df = pd.DataFrame(
        {
            "name": ["Ann", "Cara", "Cara"],
            "workout_date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)],
            "burnt_250": [True, False, False],  # Cara has workouts but none qualify
            "month": ["2024-01"] * 3,
            "calories_burned": [300, 100, 100],
        }
    )
    out = month_leaderboard(df, "2024-01", cutoff=2)  # NO all_users on purpose
    cara = out[out["name"] == "Cara"].iloc[0]
    assert int(cara["workout_days"]) == 2
    assert int(cara["qualifying_days"]) == 0
    assert int(cara["workouts_left"]) == 2
    assert bool(cara["is_winner"]) is False


def test_month_leaderboard_exact_column_set():
    """Output schema is exactly the documented set of columns.

    Kills mutations that rename a column-assignment target to a placeholder
    identifier (e.g. `out["qualifying_days"]` → `out["XXqualifying_daysXX"]`).
    Such a mutation creates a stray column that downstream value assertions
    don't notice, but a strict set comparison catches immediately.
    """
    df = _df_for_month()
    out = month_leaderboard(df, "2024-01", cutoff=2, all_users=["Ann", "Bob", "Cara"])
    assert set(out.columns) == {
        "name",
        "workout_days",
        "qualifying_days",
        "total_calories",
        "workouts_left",
        "is_winner",
        "progress",
        "rank",
    }
