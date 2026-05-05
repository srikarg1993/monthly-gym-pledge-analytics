import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

from data.source import clean, normalize_bool


def test_normalize_bool():
    assert normalize_bool("yes") is True
    assert normalize_bool("TRUE") is True
    assert normalize_bool("1") is True
    assert normalize_bool("y") is True
    assert normalize_bool("t") is True
    assert normalize_bool("no") is False
    assert normalize_bool("") is False
    assert normalize_bool(pd.NA) is False


def test_clean_missing_columns_raises():
    df = pd.DataFrame({"Timestamp": ["2024-01-01"], "You are?": ["A"]})
    with pytest.raises(ValueError):
        clean(df)


def test_clean_dedupe_keeps_latest_timestamp():
    df = pd.DataFrame(
        {
            "Timestamp": ["2024-01-01 10:00:00", "2024-01-01 12:00:00"],
            "You are?": ["Ann", "Ann"],
            "Workout date": ["2024-01-01", "2024-01-01"],
            "Burnt >= 250 calories?": ["no", "yes"],
        }
    )
    out = clean(df, dedupe=True)
    assert len(out) == 1
    assert bool(out.iloc[0]["burnt_250"]) is True


def test_clean_derives_date_fields():
    df = pd.DataFrame(
        {
            "Timestamp": ["2024-01-05 08:00:00"],
            "You are?": ["Ann"],
            "Workout date": ["2024-01-03"],
            "Burnt >= 250 calories?": ["yes"],
        }
    )
    out = clean(df, dedupe=True)
    assert out.iloc[0]["month"] == "2024-01"
    assert out.iloc[0]["dow"] == "Wednesday"
    assert out.iloc[0]["dom"] == 3
    assert out.iloc[0]["log_delay_days"] == 2


def _make_df_with_calories(calories_values):
    """Helper to build a raw DataFrame with the calories column."""
    n = len(calories_values)
    return pd.DataFrame(
        {
            "Timestamp": ["2024-01-05 08:00:00"] * n,
            "You are?": [f"Person{i}" for i in range(n)],
            "Workout date": ["2024-01-03"] * n,
            "Burnt >= 250 calories?": ["yes"] * n,
            "How many calories did you burn?": calories_values,
        }
    )


def test_clean_calories_drops_non_numeric():
    df = _make_df_with_calories(["300", "abc", ""])
    out = clean(df, dedupe=False)
    # "abc" is dropped (non-empty garbage), "" is kept as NaN
    assert len(out) == 2
    assert out.iloc[0]["calories_burned"] == 300
    assert pd.isna(out.iloc[1]["calories_burned"])


def test_clean_calories_drops_null():
    df = _make_df_with_calories(["400", pd.NA, None])
    out = clean(df, dedupe=False)
    # pd.NA and None are blank — rows are kept with NaN calories
    assert len(out) == 3
    assert out.iloc[0]["calories_burned"] == 400
    assert pd.isna(out.iloc[1]["calories_burned"])
    assert pd.isna(out.iloc[2]["calories_burned"])


def test_clean_calories_drops_outliers_above_2200():
    df = _make_df_with_calories(["500", "2200", "2201", "5000"])
    out = clean(df, dedupe=False)
    assert len(out) == 2
    assert list(out["calories_burned"]) == [500, 2200]


def test_clean_calories_met_250_flag():
    df = _make_df_with_calories(["100", "249", "250", "800"])
    out = clean(df, dedupe=False)
    assert list(out["calories_met_250"]) == [False, False, True, True]


def test_clean_without_calories_column():
    """Backward compatibility: clean works when calories column is absent."""
    df = pd.DataFrame(
        {
            "Timestamp": ["2024-01-05 08:00:00"],
            "You are?": ["Ann"],
            "Workout date": ["2024-01-03"],
            "Burnt >= 250 calories?": ["yes"],
        }
    )
    out = clean(df, dedupe=True)
    assert len(out) == 1
    assert pd.isna(out.iloc[0]["calories_burned"])
    assert pd.isna(out.iloc[0]["calories_met_250"])


def test_clean_unparseable_workout_date_yields_na_month():
    df = pd.DataFrame(
        {
            "Timestamp": ["2024-01-05 08:00:00", "2024-01-06 09:00:00"],
            "You are?": ["Ann", "Bob"],
            "Workout date": ["2024-01-03", "not-a-date"],
            "Burnt >= 250 calories?": ["yes", "yes"],
        }
    )
    out = clean(df, dedupe=False)
    bob_month = out[out["name"] == "Bob"].iloc[0]["month"]
    assert pd.isna(bob_month)
    assert "NaT" not in set(out["month"].dropna().unique())
