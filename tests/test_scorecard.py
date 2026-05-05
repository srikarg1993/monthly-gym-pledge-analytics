import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

from ui.common import classify_lazy_zone, pack_lazy_bubbles
from ui.scorecard import (
    _build_close_call_data,
    _build_status_mix_df,
    _build_streak_wave_df,
    _build_style_balance_df,
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
    counts = dict(zip(out["Status"], out["People"], strict=False))

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
            "name": ["Ava", "Ben", "Cara", "Dee", "Eli"],
            "first_half": [6, 3, 2, 8, 5],
            "second_half": [1, 3, 7, 1, 6],
            "style": ["Front-loader", "Balanced", "Crammer", "Front-loader", "Balanced"],
        }
    )

    out = _build_style_balance_df(fl)

    # Chart top -> bottom: Front-loaders (by First Half DESC), Balanced (by
    # Total DESC), Crammers (by Second Half ASC). The dataframe is returned
    # in this same order; Altair's categorical y-axis with `sort=` keeps the
    # first row at the top of the chart.
    assert out["Name"].tolist() == ["Dee", "Ava", "Eli", "Ben", "Cara"]


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


def test_classify_lazy_zone_matches_legacy_bucket_boundaries():
    # Boundaries match legacy alt_delay_runway_chart cuts: <=0.5, <=1.5, >1.5.
    assert classify_lazy_zone(0.0) == "on_it"
    assert classify_lazy_zone(0.5) == "on_it"
    assert classify_lazy_zone(0.51) == "catching_up"
    assert classify_lazy_zone(1.5) == "catching_up"
    assert classify_lazy_zone(1.51) == "falling_behind"
    assert classify_lazy_zone(7.0) == "falling_behind"


def test_pack_lazy_bubbles_assigns_zone_first_name_and_positions():
    df = pd.DataFrame(
        {
            "Name": ["Ava Stone", "Ben Park", "Cara Lin", "Drew Fox"],
            "Avg. Log Delay (Days)": [0.0, 0.8, 2.4, 3.0],
            "Logged Workouts": [10, 6, 4, 2],
        }
    )

    out = pack_lazy_bubbles(
        df,
        name_col="Name",
        delay_col="Avg. Log Delay (Days)",
        size_col="Logged Workouts",
    )

    by_name = {row["Name"]: row for _, row in out.iterrows()}
    assert by_name["Ava Stone"]["Zone"] == "on_it"
    assert by_name["Ben Park"]["Zone"] == "catching_up"
    assert by_name["Cara Lin"]["Zone"] == "falling_behind"
    assert by_name["Drew Fox"]["Zone"] == "falling_behind"
    assert by_name["Ava Stone"]["FirstName"] == "Ava"

    for _, row in out.iterrows():
        assert pd.notna(row["x"]) and pd.notna(row["y"])


def test_pack_lazy_bubbles_handles_empty_input():
    empty = pd.DataFrame(columns=["Name", "Avg. Log Delay (Days)", "Logged Workouts"])
    out = pack_lazy_bubbles(
        empty,
        name_col="Name",
        delay_col="Avg. Log Delay (Days)",
        size_col="Logged Workouts",
    )

    assert out.empty
    assert {"Zone", "ZoneLabel", "FirstName", "x", "y"}.issubset(out.columns)
