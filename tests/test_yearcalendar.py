"""Tests for yearcalendar UI helpers (full-year stats and chart data)."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

from ui.yearcalendar import (
    _altair_monthly_chart,
    _name_col,
    _year_from_month_str,
    _year_stats_for_person,
)


def test_name_col_uses_name():
    df = pd.DataFrame(columns=["name", "workout_date"])
    assert _name_col(df) == "name"


def test_name_col_uses_Name_when_no_name():
    df = pd.DataFrame(columns=["Name", "workout_date"])
    assert _name_col(df) == "Name"


def test_year_from_month_str_parses_yyyy_mm():
    assert _year_from_month_str("2024-06") == 2024
    assert _year_from_month_str("2023-01") == 2023


def test_year_from_month_str_invalid_returns_current_year():
    with patch("ui.yearcalendar.today_app") as m:
        m.return_value = type("T", (), {"year": 2025})()
        assert _year_from_month_str(None) == 2025
        assert _year_from_month_str("invalid") == 2025


def test_year_stats_for_person_empty_df():
    workout_days, qualifying_days, streak, monthly_df = _year_stats_for_person(pd.DataFrame(), "Ann", "name", 2024)
    assert workout_days == 0
    assert qualifying_days == 0
    assert streak == 0
    assert monthly_df.empty


def test_year_stats_for_person_none_df():
    workout_days, qualifying_days, streak, monthly_df = _year_stats_for_person(None, "Ann", "name", 2024)
    assert workout_days == 0
    assert qualifying_days == 0
    assert streak == 0
    assert monthly_df.empty


def test_year_stats_for_person_computes_totals_and_streak():
    df_year = pd.DataFrame(
        {
            "name": ["Ann", "Ann", "Ann", "Ann", "Ann"],
            "workout_date": [
                date(2024, 1, 1),
                date(2024, 1, 2),
                date(2024, 1, 3),
                date(2024, 2, 1),
                date(2024, 2, 2),
            ],
            "burnt_250": [True, True, True, False, True],
            "month": ["2024-01", "2024-01", "2024-01", "2024-02", "2024-02"],
        }
    )
    workout_days, qualifying_days, streak, monthly_df = _year_stats_for_person(df_year, "Ann", "name", 2024)
    assert workout_days == 5
    assert qualifying_days == 4
    assert streak == 3  # Jan 1, 2, 3 consecutive qualifying
    assert len(monthly_df) == 12
    jan = monthly_df[monthly_df["Month"] == "Jan"].iloc[0]
    assert jan["Workouts"] == 3
    assert jan["Qualifying"] == 3
    feb = monthly_df[monthly_df["Month"] == "Feb"].iloc[0]
    assert feb["Workouts"] == 2
    assert feb["Qualifying"] == 1


def test_year_stats_for_person_unknown_person_returns_zeros_and_empty_monthly():
    df_year = pd.DataFrame(
        {"name": ["Bob"], "workout_date": [date(2024, 1, 1)], "burnt_250": [True], "month": ["2024-01"]}
    )
    workout_days, qualifying_days, streak, monthly_df = _year_stats_for_person(df_year, "Ann", "name", 2024)
    assert workout_days == 0
    assert qualifying_days == 0
    assert streak == 0
    assert monthly_df.empty


def test_altair_monthly_chart_builds_native_altair_chart():
    """Yearbook now uses native Altair instead of an ApexCharts CDN embed.

    The chart spec must include both series and the month names from the
    input DataFrame.
    """
    monthly_df = pd.DataFrame(
        {
            "Month": ["Jan", "Feb"],
            "Workouts": [5, 3],
            "Qualifying": [4, 2],
        }
    )
    chart = _altair_monthly_chart(monthly_df)
    spec = chart.to_dict()
    # Spec must mention both months and both series labels.
    spec_text = repr(spec)
    assert "Jan" in spec_text
    assert "Feb" in spec_text
    assert "Workouts" in spec_text
    assert "Qualifying" in spec_text


def test_altair_monthly_chart_handles_empty_input():
    chart = _altair_monthly_chart(pd.DataFrame())
    # Should not raise and should produce a valid (empty) Altair spec.
    assert chart.to_dict() is not None
