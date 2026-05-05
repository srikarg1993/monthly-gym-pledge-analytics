"""Edge-case tests added during the 2026-05-05 audit pass.

Covers branches that were not exercised by existing test files:
- `longest_streak` with duplicates, single date, and `None` values.
- `frontload_vs_cram` on an empty DataFrame.
- `lazy_logger_score` with a single user.
- `month_bounds` for a leap-year February and a 31-day month.
- `winner_cutoff_for_month` with malformed override values.
- `normalize_bool` over the full truthy / falsy / NA matrix.
"""

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

from config.globals import WINNER_CUTOFF, winner_cutoff_for_month  # noqa: E402
from data.metrics import (  # noqa: E402
    frontload_vs_cram,
    lazy_logger_score,
    longest_streak,
    month_bounds,
)
from data.source import _month_label, normalize_bool  # noqa: E402


class TestLongestStreak:
    def test_empty(self):
        assert longest_streak([]) == 0

    def test_single_date(self):
        assert longest_streak([date(2024, 1, 1)]) == 1

    def test_duplicates_collapse(self):
        # Duplicates should be deduplicated before computing the streak.
        ds = [date(2024, 1, 1), date(2024, 1, 1), date(2024, 1, 2)]
        assert longest_streak(ds) == 2

    def test_drops_none_values(self):
        ds = [date(2024, 1, 1), None, date(2024, 1, 2), None]
        assert longest_streak(ds) == 2

    def test_unsorted_input(self):
        ds = [date(2024, 1, 5), date(2024, 1, 3), date(2024, 1, 4)]
        assert longest_streak(ds) == 3

    def test_long_run_with_gap(self):
        ds = [
            date(2024, 1, 1),
            date(2024, 1, 2),
            date(2024, 1, 3),
            date(2024, 1, 7),
            date(2024, 1, 8),
        ]
        assert longest_streak(ds) == 3


class TestFrontloadVsCram:
    def test_empty_dataframe(self):
        out = frontload_vs_cram(pd.DataFrame())
        assert out.empty


class TestLazyLoggerScore:
    def test_single_user(self):
        df = pd.DataFrame(
            {
                "name": ["Solo"],
                "log_delay_days": [2.5],
                "workout_date": [date(2024, 1, 1)],
                "timestamp": [pd.Timestamp("2024-01-04")],
            }
        )
        out = lazy_logger_score(df)
        assert list(out["name"]) == ["Solo"]
        assert out.iloc[0]["avg_log_delay_days"] == 2.5

    def test_drops_rows_missing_timestamp_or_workout_date(self):
        df = pd.DataFrame(
            {
                "name": ["Ann", "Ann", "Bob"],
                "log_delay_days": [1.0, 2.0, 5.0],
                "workout_date": [date(2024, 1, 1), None, date(2024, 1, 1)],
                "timestamp": [
                    pd.Timestamp("2024-01-02"),
                    pd.Timestamp("2024-01-03"),
                    pd.NaT,
                ],
            }
        )
        out = lazy_logger_score(df)
        assert list(out["name"]) == ["Ann"]
        assert out.iloc[0]["avg_log_delay_days"] == 1.0


class TestMonthBounds:
    def test_leap_year_february(self):
        start, end = month_bounds("2024-02")
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_non_leap_february(self):
        start, end = month_bounds("2025-02")
        assert end == date(2025, 2, 28)

    def test_thirty_one_day_month(self):
        start, end = month_bounds("2024-07")
        assert start == date(2024, 7, 1)
        assert end == date(2024, 7, 31)

    def test_thirty_day_month(self):
        _, end = month_bounds("2024-04")
        assert end == date(2024, 4, 30)


class TestWinnerCutoffForMonth:
    def test_known_override(self):
        # WINNER_CUTOFF_BY_MONTH currently has 2026-02 -> 15.
        assert winner_cutoff_for_month("2026-02") == 15

    def test_unknown_month_falls_back_to_default(self):
        assert winner_cutoff_for_month("9999-12") == WINNER_CUTOFF

    def test_returns_default_for_none_input(self):
        # Passing through `str(None)` produces "None", which is not in the
        # override dict, so we expect the default.
        assert winner_cutoff_for_month(None) == WINNER_CUTOFF

    def test_clamped_to_minimum_one(self, monkeypatch):
        from config import globals as g
        monkeypatch.setitem(g.WINNER_CUTOFF_BY_MONTH, "2099-01", 0)
        assert winner_cutoff_for_month("2099-01") == 1

    def test_invalid_override_falls_back(self, monkeypatch):
        from config import globals as g
        monkeypatch.setitem(g.WINNER_CUTOFF_BY_MONTH, "2099-02", "not-a-number")
        assert winner_cutoff_for_month("2099-02") == WINNER_CUTOFF


class TestNormalizeBool:
    @pytest.mark.parametrize(
        "value", ["yes", "YES", "True", " 1 ", "y", "T", "true"]
    )
    def test_truthy(self, value):
        assert normalize_bool(value) is True

    @pytest.mark.parametrize("value", ["no", "false", "0", "n", "f", "", "maybe"])
    def test_falsy(self, value):
        assert normalize_bool(value) is False

    def test_na(self):
        assert normalize_bool(pd.NA) is False
        assert normalize_bool(None) is False
        assert normalize_bool(float("nan")) is False


class TestMonthLabel:
    def test_well_formed(self):
        assert _month_label("2024-01") == "January 2024"
        assert _month_label("2024-12") == "December 2024"

    def test_malformed_returns_empty(self):
        assert _month_label("not-a-month") == ""
        assert _month_label("2024-13") == ""
        assert _month_label("") == ""
