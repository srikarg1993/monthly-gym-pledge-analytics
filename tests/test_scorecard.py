import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

from ui.scorecard import (
    _build_close_call_data,
    _build_streak_wave_df,
    _build_style_balance_df,
    _build_status_mix_df,
)


def test_build_status_mix_df_buckets_people_correctly():
    lb = pd.DataFrame(
        {
            "name": ["Ava", "Ben", "Cara", "Drew", "Eli"],
            "qualifying_days": [16, 15, 14, 9, 4],
            "workout_days": [18, 15, 17, 16, 5],
        }
    )

    out = _build_status_mix_df(lb, cutoff=16)
    counts = dict(zip(out["Status"], out["People"]))

    assert counts == {
        "Winner": 1,
        "1-2 away": 2,
        "Workout-rich": 1,
        "Other": 1,
    }
    assert out["Share"].sum() == 1.0


def test_build_streak_wave_df_resets_after_break_in_streak():
    df_month = pd.DataFrame(
        {
            "name": ["Ava", "Ava", "Ava"],
            "workout_date": ["2024-01-01", "2024-01-02", "2024-01-04"],
            "burnt_250": [True, True, True],
            "month": ["2024-01", "2024-01", "2024-01"],
        }
    )

    out = _build_streak_wave_df(df_month, "Ava")

    assert out.head(4)["Streak"].tolist() == [1, 2, 0, 1]
    assert out.head(4)["Qualifying"].tolist() == [True, True, False, True]
    assert out.iloc[-1]["Day"] == 31


def test_build_style_balance_df_sorts_from_front_loaded_to_crammer():
    fl = pd.DataFrame(
        {
            "name": ["Ava", "Ben", "Cara"],
            "first_half": [6, 3, 2],
            "second_half": [1, 3, 7],
            "style": ["Front-loader", "Balanced", "Crammer"],
        }
    )

    out = _build_style_balance_df(fl)

    assert out["Name"].tolist() == ["Ava", "Ben", "Cara"]
    assert out["Balance"].tolist() == [-5, 0, 5]


def test_build_close_call_data_separates_close_calls_and_workout_rich():
    lb = pd.DataFrame(
        {
            "name": ["Ava", "Ben", "Cara", "Drew", "Eli"],
            "qualifying_days": [15, 14, 13, 16, 7],
            "workout_days": [16, 17, 16, 18, 10],
            "is_winner": [False, False, False, True, False],
        }
    )

    close_calls, workout_rich = _build_close_call_data(lb, cutoff=16)

    assert close_calls["Name"].tolist() == ["Ava", "Ben"]
    assert close_calls["Bucket"].tolist() == ["1 away", "2 away"]
    assert workout_rich["Name"].tolist() == ["Cara"]
    assert workout_rich.iloc[0]["Bucket"] == "Workout-rich"
