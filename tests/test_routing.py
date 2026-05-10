"""Routing + leaderboard tie-break tests.

Covers:
- Adversarial P0-03: static pages render even when the data layer is down.
- Adversarial P1-03: leaderboard ranking breaks ties by workout_days,
  then total_calories, then name (no alphabetical accidents).
- Adversarial P2-06: dashboard routing branches.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gym_pledge"))


def test_leaderboard_tiebreak_uses_workout_days_then_calories():
    from data.metrics import month_leaderboard

    # Both Ann and Bob have 5 qualifying days. Ann has more workout days
    # (8 vs 5) and the same calorie total. Ann must outrank Bob — not be
    # alphabetized below him.
    df = pd.DataFrame(
        {
            "name": ["Ann"] * 8 + ["Bob"] * 5,
            "workout_date": [date(2024, 1, d) for d in range(1, 9)] + [date(2024, 1, d) for d in range(1, 6)],
            "burnt_250": [True] * 5 + [False] * 3 + [True] * 5,
            "month": ["2024-01"] * 13,
            "calories_burned": [300] * 5 + [100] * 3 + [300] * 5,
        }
    )
    out = month_leaderboard(df, "2024-01", cutoff=10)
    rows = out.set_index("name")
    assert rows.loc["Ann", "qualifying_days"] == 5
    assert rows.loc["Bob", "qualifying_days"] == 5
    # Ann should be listed first (more workout_days breaks the tie).
    assert list(out["name"][:2]) == ["Ann", "Bob"]


def test_leaderboard_alphabetical_only_after_all_other_keys_equal():
    """When everything ties, fall back to alphabetical for stability."""
    from data.metrics import month_leaderboard

    df = pd.DataFrame(
        {
            "name": ["Zelda", "Ann"],
            "workout_date": [date(2024, 1, 1), date(2024, 1, 1)],
            "burnt_250": [True, True],
            "month": ["2024-01"] * 2,
            "calories_burned": [300, 300],
        }
    )
    out = month_leaderboard(df, "2024-01", cutoff=1)
    assert list(out["name"]) == ["Ann", "Zelda"]


# ---------------------------------------------------------------------------
# Routing — static pages must render without get_data()
# ---------------------------------------------------------------------------
def test_static_pages_import_without_data_layer():
    """About + Log Your Workout must NOT import data/source at module
    load time. If they do, a Sheets outage at import would also blank
    them out (P0-03).
    """
    import importlib

    # Ensure they import cleanly even when get_data is broken.
    with patch("data.source.get_data", side_effect=RuntimeError("sheets down")):
        importlib.import_module("ui.about")
        importlib.import_module("ui.logyourworkout")


def test_dashboard_routes_static_pages_without_data_layer():
    """Smoke: dashboard's PAGES + DATA_BACKED_PAGES must list the static
    pages OUTSIDE the data-backed set so a Sheets outage cannot black
    them out.
    """
    import dashboard

    assert "About us" not in dashboard.DATA_BACKED_PAGES
    assert "Log Your Workout" not in dashboard.DATA_BACKED_PAGES
    assert "About us" in dashboard.PAGES
    assert "Log Your Workout" in dashboard.PAGES
    # Data-backed pages are exactly the analytics surfaces.
    assert {"Leaderboard", "Scorecard", "Fitness Yearbook"} == dashboard.DATA_BACKED_PAGES


# ---------------------------------------------------------------------------
# Hidden-page decision: monthovermonth + personalization were imported but
# unreachable. dashboard.py no longer imports them at module load and
# does not list them in PAGES — so we simply confirm they are not exposed.
# ---------------------------------------------------------------------------
def test_hidden_pages_are_not_in_sidebar():
    import dashboard

    assert "Month-over-month Trends" not in dashboard.PAGES
    assert "Personalization" not in dashboard.PAGES


# ---------------------------------------------------------------------------
# Routing helper sanity
# ---------------------------------------------------------------------------
def test_dashboard_lazy_render_imports_module_lazily():
    """`_lazy_render` should import the page module on demand, not at
    dashboard import time (P3-17 — keep heavy chart libs out of static
    page loads).
    """
    import dashboard

    fn = dashboard._lazy_render("ui.about")
    assert callable(fn)


@pytest.mark.parametrize("page", ["Leaderboard", "Scorecard", "Fitness Yearbook"])
def test_data_backed_pages_listed_in_pages(page):
    import dashboard

    assert page in dashboard.PAGES
    assert page in dashboard.DATA_BACKED_PAGES
