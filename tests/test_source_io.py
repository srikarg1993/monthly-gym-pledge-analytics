"""Boundary tests for `data.source` get_users / get_data and the
`CleanQualityReport`. Closes the source-coverage gap flagged as P2-01
in the 2026-05-10 adversarial review and exercises the failure-mode
branches added in response to P0-04 / P1-07 / P1-05.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))

import data.source as source_mod
from data.source import (
    CleanQualityReport,
    GetUsersResult,
    GetUsersStatus,
    clean,
    get_users,
    normalize_name,
)


# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------
def test_normalize_name_strips_and_collapses_whitespace():
    assert normalize_name("  Ann   Smith ") == "Ann Smith"


def test_normalize_name_handles_missing():
    assert normalize_name(None) == ""
    assert normalize_name(pd.NA) == ""
    assert normalize_name(float("nan")) == ""
    assert normalize_name("nan") == ""
    assert normalize_name("<NA>") == ""


# ---------------------------------------------------------------------------
# get_users — branches per failure mode
# ---------------------------------------------------------------------------
def _patch_sheet(df: pd.DataFrame):
    """Patch the cached sheet reader to return ``df`` and clear caches."""
    get_users.clear()
    return patch.object(source_mod, "read_google_sheet_as_df", return_value=df)


def test_get_users_read_error_returns_typed_failure():
    get_users.clear()
    with patch.object(source_mod, "read_google_sheet_as_df", side_effect=RuntimeError("boom")):
        result = get_users("2026-05")
    assert isinstance(result, GetUsersResult)
    assert result.status is GetUsersStatus.READ_ERROR
    assert result.users == []
    assert "RuntimeError" in result.message


def test_get_users_empty_sheet():
    with _patch_sheet(pd.DataFrame()):
        result = get_users("2026-05")
    assert result.status is GetUsersStatus.EMPTY_SHEET
    assert result.users == []


def test_get_users_missing_name_column():
    df = pd.DataFrame({"Wrong": ["Ann"]})
    with _patch_sheet(df):
        result = get_users("2026-05")
    assert result.status is GetUsersStatus.MISSING_NAME_COLUMN
    assert result.users == []


def test_get_users_missing_month_column_does_not_silently_fall_back():
    """Adversarial P0-04: when the month column is missing we must NOT
    return everyone. We must surface the degradation so the caller can
    decide how to handle it.
    """
    df = pd.DataFrame({"Participant": ["Ann", "Bob"]})  # no May 2026 column
    with _patch_sheet(df):
        result = get_users("2026-05")
    assert result.status is GetUsersStatus.MISSING_MONTH_COLUMN
    assert result.users == []
    assert "May 2026" in result.message


def test_get_users_no_active_users_after_filter():
    df = pd.DataFrame({"Participant": ["Ann", "Bob"], "May 2026": ["Out", "Out"]})
    with _patch_sheet(df):
        result = get_users("2026-05")
    assert result.status is GetUsersStatus.NO_ACTIVE_USERS
    assert result.users == []


def test_get_users_ok_filters_in_users_for_month():
    df = pd.DataFrame(
        {
            "Participant": [" Ann ", "Bob", "Cara"],
            "May 2026": ["In", "Out", "in"],
        }
    )
    with _patch_sheet(df):
        result = get_users("2026-05")
    assert result.status is GetUsersStatus.OK
    assert result.ok is True
    # Whitespace-stripped via normalize_name; case-insensitive "In" match
    assert set(result.users) == {"Ann", "Cara"}


def test_get_users_ok_without_month_argument():
    df = pd.DataFrame({"Participant": ["Ann", "Bob"]})
    with _patch_sheet(df):
        result = get_users(None)
    assert result.status is GetUsersStatus.OK
    assert set(result.users) == {"Ann", "Bob"}


def test_get_users_result_back_compat_truthiness_and_iteration():
    """`if users:` and `list(users)` style code from the old API still works."""
    result = GetUsersResult(users=["Ann", "Bob"], status=GetUsersStatus.OK)
    assert bool(result) is True
    assert list(result) == ["Ann", "Bob"]
    assert len(result) == 2

    empty = GetUsersResult(users=[], status=GetUsersStatus.EMPTY_SHEET)
    assert bool(empty) is False
    assert list(empty) == []
    assert len(empty) == 0


# ---------------------------------------------------------------------------
# clean() data-quality report (P1-05)
# ---------------------------------------------------------------------------
def _make_raw_df(rows: list[dict]) -> pd.DataFrame:
    cols = ["Timestamp", "You are?", "Workout date", "Burnt >= 250 calories?", "How many calories did you burn?"]
    return pd.DataFrame([{c: r.get(c) for c in cols} for r in rows], columns=cols)


def test_clean_attaches_quality_report_with_zero_drops_for_clean_input(monkeypatch):
    from datetime import date as _date

    monkeypatch.setattr(source_mod, "today_app", lambda: _date(2024, 2, 1))
    raw = _make_raw_df(
        [
            {
                "Timestamp": "2024-01-15 08:00:00",
                "You are?": "Ann",
                "Workout date": "2024-01-15",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            }
        ]
    )
    out = clean(raw)
    report = out.attrs.get("quality_report")
    assert isinstance(report, CleanQualityReport)
    assert report.rows_in == 1
    assert report.rows_out == 1
    assert report.total_dropped == 0


def test_clean_quality_report_counts_each_drop_reason(monkeypatch):
    from datetime import date as _date

    monkeypatch.setattr(source_mod, "today_app", lambda: _date(2024, 2, 1))
    raw = _make_raw_df(
        [
            {
                "Timestamp": "",  # NaT timestamp
                "You are?": "Ann",
                "Workout date": "2024-01-15",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            },
            {
                "Timestamp": "2024-02-10 08:00:00",
                "You are?": "  ",  # blank name
                "Workout date": "2024-01-15",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            },
            {
                "Timestamp": "2024-02-10 08:00:00",
                "You are?": "Bob",
                "Workout date": "1999-03-15",  # too old
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            },
            {
                "Timestamp": "2024-02-10 08:00:00",
                "You are?": "Cara",
                "Workout date": "2024-03-01",  # future
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            },
            {
                "Timestamp": "2024-02-10 08:00:00",
                "You are?": "Dee",
                "Workout date": "2024-01-20",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "abc",  # garbage calories
            },
            {
                "Timestamp": "2024-02-10 08:00:00",
                "You are?": "Eli",
                "Workout date": "2024-01-20",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "9999",  # out of range
            },
            {
                "Timestamp": "2024-02-10 08:00:00",
                "You are?": "Fay",
                "Workout date": "2024-01-15",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "400",
            },
        ]
    )
    out = clean(raw)
    report = out.attrs["quality_report"]
    assert report.dropped_blank_name == 1
    assert report.dropped_nat_timestamp == 1
    assert report.dropped_too_old == 1
    assert report.dropped_future == 1
    assert report.dropped_bad_calories == 1
    assert report.dropped_calories_out_of_range == 1
    assert report.rows_out == 1  # only Fay survives


def test_clean_calories_met_250_is_na_when_calories_blank(monkeypatch):
    """Adversarial P1-02: blank calories must surface as pd.NA, not False."""
    from datetime import date as _date

    monkeypatch.setattr(source_mod, "today_app", lambda: _date(2024, 2, 1))
    raw = _make_raw_df(
        [
            {
                "Timestamp": "2024-01-15 08:00:00",
                "You are?": "Ann",
                "Workout date": "2024-01-15",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "",
            },
            {
                "Timestamp": "2024-01-15 09:00:00",
                "You are?": "Bob",
                "Workout date": "2024-01-15",
                "Burnt >= 250 calories?": "no",
                "How many calories did you burn?": "100",
            },
        ]
    )
    out = clean(raw, dedupe=False)
    ann = out[out["name"] == "Ann"].iloc[0]
    bob = out[out["name"] == "Bob"].iloc[0]
    assert pd.isna(ann["calories_met_250"])  # blank -> NA, not False
    assert bool(bob["calories_met_250"]) is False


def test_clean_log_delay_is_clamped_to_zero(monkeypatch):
    """Adversarial P1-06: timezone-grace artifacts must not produce
    negative log_delay_days that skew Lazy Logger averages.
    """
    from datetime import date as _date

    monkeypatch.setattr(source_mod, "today_app", lambda: _date(2024, 2, 1))
    raw = _make_raw_df(
        [
            {
                "Timestamp": "2024-01-15 08:00:00",
                "You are?": "Ann",
                # Workout date == timestamp + 1 day (within grace window).
                "Workout date": "2024-01-16",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            }
        ]
    )
    out = clean(raw, dedupe=False)
    assert int(out.iloc[0]["log_delay_days"]) >= 0


def test_clean_dow_str_and_dow_num_int():
    """Domain dual representation: dow is the day-name string;
    dow_num is the integer (Mon=0..Sun=6).
    """
    raw = _make_raw_df(
        [
            {
                "Timestamp": "2024-01-15 08:00:00",
                "You are?": "Ann",
                "Workout date": "2024-01-15",  # Monday
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            }
        ]
    )
    out = clean(raw)
    assert out.iloc[0]["dow"] == "Monday"
    assert int(out.iloc[0]["dow_num"]) == 0


# ---------------------------------------------------------------------------
# Schema contract (P2-08): clean() output column set is part of the
# documented domain model in agents.md. A drift here means the docs lie.
# ---------------------------------------------------------------------------
EXPECTED_CLEAN_COLUMNS = {
    # Raw passthrough / temporary
    "name_raw",
    "workout_date_raw",
    "burnt_250_raw",
    "calories_raw",
    "timestamp_date",
    "workout_dt",
    # Canonical domain columns
    "name",
    "timestamp",
    "workout_date",
    "burnt_250",
    "calories_burned",
    "calories_met_250",
    "month",
    "dow",
    "dow_num",
    "dom",
    "log_delay_days",
    "any_workout",
}


def test_clean_output_schema_matches_documented_domain_model():
    raw = _make_raw_df(
        [
            {
                "Timestamp": "2024-01-15 08:00:00",
                "You are?": "Ann",
                "Workout date": "2024-01-15",
                "Burnt >= 250 calories?": "yes",
                "How many calories did you burn?": "300",
            }
        ]
    )
    out = clean(raw)
    actual = set(out.columns)
    missing = EXPECTED_CLEAN_COLUMNS - actual
    assert not missing, f"Missing documented columns: {missing}"


# ---------------------------------------------------------------------------
# Doc/code drift contract (P2-08): About page constants must be the
# config constants. Without this test the two can drift again.
# ---------------------------------------------------------------------------
def test_about_page_constants_are_sourced_from_config():
    from config import globals as cfg
    from ui import about

    assert about.PLEDGE_AMOUNT == cfg.PLEDGE_AMOUNT_USD
    assert about.QUALIFYING_DAYS == cfg.QUALIFYING_DAYS
    assert about.DAILY_CALORIE_TARGET == cfg.DAILY_CALORIE_TARGET
    assert about.VENMO_LINK == cfg.VENMO_LINK
    assert about.VENMO_HANDLE == cfg.VENMO_HANDLE


def test_logyourworkout_uses_config_form_urls():
    from config import globals as cfg
    from ui import logyourworkout

    # The page renders these URLs verbatim, so a smoke import alone is
    # not enough — we assert the page module pulls them from config.
    src = Path(logyourworkout.__file__).read_text(encoding="utf-8")
    assert "WORKOUT_FORM_URL" in src
    assert "WORKOUT_FORM_EMBED_URL" in src
    # And that the config still defines them (not just the alias).
    assert cfg.WORKOUT_FORM_URL.startswith("https://")
    assert cfg.WORKOUT_FORM_EMBED_URL.startswith("https://")


# ---------------------------------------------------------------------------
# Hostile-input safety (P2-05): every dynamic value rendered through raw
# HTML/SVG must be escaped via ui.escape.safe_html / safe_attr.
# ---------------------------------------------------------------------------
def test_safe_html_escapes_script_payload():
    from ui.escape import safe_html

    payload = "<script>alert(1)</script>"
    escaped = safe_html(payload)
    assert "<" not in escaped
    assert "&lt;" in escaped
    assert "script" in escaped


def test_safe_html_escapes_quote_attribute_payload():
    from ui.escape import safe_attr

    payload = '" onerror="alert(1)'
    escaped = safe_attr(payload)
    assert "&quot;" in escaped or "&#x27;" in escaped or '"' not in escaped


def test_styled_table_escapes_hostile_cell_values(monkeypatch):
    """`render_styled_table` is the one place that builds <td> values from a
    DataFrame. A hostile cell must be escaped before being concatenated
    into the rendered HTML.
    """
    captured = {}

    def fake_markdown(text, unsafe_allow_html=False):
        captured["text"] = text

    import ui.common as common

    monkeypatch.setattr(common.st, "markdown", fake_markdown)
    df = pd.DataFrame(
        {
            "Name": ["<script>alert(1)</script>"],
            "Score": ["7"],
        }
    )
    common.render_styled_table(df)
    rendered = captured.get("text", "")
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_safe_html_handles_none_and_numbers():
    from ui.escape import safe_html

    assert safe_html(None) == ""
    assert safe_html(42) == "42"
    assert safe_html(3.14) == "3.14"


# ---------------------------------------------------------------------------
# CleanQualityReport public surface
# ---------------------------------------------------------------------------
def test_clean_quality_report_as_dict_includes_total():
    r = CleanQualityReport(rows_in=10, rows_out=8, dropped_blank_name=2)
    d = r.as_dict()
    assert d["rows_in"] == 10
    assert d["rows_out"] == 8
    assert d["dropped_blank_name"] == 2
    assert d["total_dropped"] == 2


# ---------------------------------------------------------------------------
# Roster-only current-month leaderboard (P2-07)
# ---------------------------------------------------------------------------
def test_month_leaderboard_with_roster_and_no_workouts_yet():
    """Common first-day-of-month state: roster has people, the form has
    zero rows for the month yet. Every roster member must still appear
    on the leaderboard (with zeros), not be silently absent.
    """
    from datetime import date as _date

    from data.metrics import month_leaderboard

    # Non-empty workouts DataFrame, but no rows match the requested month.
    df = pd.DataFrame(
        {
            "name": ["Zed"],
            "workout_date": [_date(2024, 1, 1)],
            "burnt_250": [True],
            "month": ["2024-01"],
            "calories_burned": [300],
        }
    )
    out = month_leaderboard(df, "2026-05", cutoff=16, all_users=["Ann", "Bob", "Cara"])
    assert set(out["name"]) == {"Ann", "Bob", "Cara"}
    assert (out["workout_days"] == 0).all()
    assert (out["qualifying_days"] == 0).all()
    assert (out["is_winner"] == False).all()  # noqa: E712


# ---------------------------------------------------------------------------
# clean() schema check (still raises for missing columns)
# ---------------------------------------------------------------------------
def test_clean_raises_for_missing_required_columns():
    df = pd.DataFrame({"Timestamp": ["2024-01-01"]})
    with pytest.raises(ValueError):
        clean(df)
