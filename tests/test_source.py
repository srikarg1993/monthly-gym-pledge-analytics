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
