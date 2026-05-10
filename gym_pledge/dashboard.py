"""Dashboard entry point.

Routes the active sidebar tab to one of the page renderers and only
loads Google-Sheet-backed data when the active page actually needs it.
That way the static pages (About, Log Your Workout) keep working when
Sheets is unavailable — adversarial review P0-03.

The module is structured so importing it (e.g. from tests) does NOT
execute Streamlit calls. All side-effecting work lives in :func:`main`,
which is invoked under ``if __name__ == "__main__"`` — the condition
Streamlit uses when running a script as the entry point.
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Callable
from pathlib import Path

import streamlit as st

from app_time import current_month_str
from config.globals import winner_cutoff_for_month
from data.source import GetUsersStatus

# =========================================================
# Sidebar navigation table — public so tests can introspect.
# =========================================================
PAGES: list[str] = [
    "About us",
    "Leaderboard",
    "Scorecard",
    "Fitness Yearbook",
    "Log Your Workout",
]

# Pages that need the workouts DataFrame. Anything not in this set must
# render without calling `get_data()` so a Sheets outage cannot black out
# the whole app.
DATA_BACKED_PAGES: set[str] = {"Leaderboard", "Scorecard", "Fitness Yearbook"}


# =========================================================
# CSS loader (cached — adversarial P3-13)
# =========================================================
@st.cache_data(show_spinner=False)
def _load_css_text(rel_path: str) -> str:
    css_path = Path(__file__).resolve().parent / rel_path
    return css_path.read_text(encoding="utf-8")


def _inject_css(rel_path: str) -> None:
    st.markdown(f"<style>{_load_css_text(rel_path)}</style>", unsafe_allow_html=True)


# =========================================================
# Page lazy-loader (adversarial P3-17 — don't import every page on
# every run, especially Matplotlib-heavy ones)
# =========================================================
def _lazy_render(module_name: str) -> Callable:
    module = importlib.import_module(module_name)
    return module.render


def _render_sidebar() -> str:
    with st.sidebar:
        st.markdown("### Navigation")
        return st.radio(
            "Page",
            PAGES,
            key="tab",
            label_visibility="collapsed",
        )


def _month_selector_label(label: str) -> None:
    st.markdown(
        f"<div style='white-space:nowrap; font-size:18px; font-weight:600'>{label}</div>",
        unsafe_allow_html=True,
    )


def main() -> None:
    """Render the dashboard. Side-effecting; safe to skip during import."""
    st.set_page_config(
        page_title="Monthly Fitness Pledge",
        page_icon="💪",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css("styles/theme.css")

    tab = _render_sidebar()
    st.markdown("# Monthly Fitness Pledge")

    # Static pages: render WITHOUT touching the Google Sheet so a Sheets
    # outage cannot black out About / Log Your Workout (P0-03).
    if tab == "About us":
        _lazy_render("ui.about")()
        st.stop()
        return
    if tab == "Log Your Workout":
        _lazy_render("ui.logyourworkout")()
        st.stop()
        return

    # Lazy import to keep static pages independent of the data layer.
    from data.metrics import month_leaderboard
    from data.source import get_data, get_users

    df = get_data()

    months = sorted([m for m in df["month"].dropna().unique().tolist()])
    if not months:
        st.warning("No workouts found yet.")
        st.stop()
        return

    cur = current_month_str()
    default_idx = months.index(cur) if cur in months else (len(months) - 1)

    # Page-specific selectors. Yearbook gets a YEAR selector (P4-03).
    header_cols = st.columns([1, 0.28], gap="large")
    with header_cols[0]:
        if tab == "Leaderboard":
            st.caption("Live current-month standings.")
        elif tab == "Scorecard":
            st.caption("Pick a month to see how the group did.")
        elif tab == "Fitness Yearbook":
            st.caption("Pick a year to browse the calendar grid.")
    with header_cols[1]:
        if tab == "Scorecard":
            _month_selector_label("Month")
            month_selected = st.selectbox("Month", months, index=default_idx, label_visibility="collapsed")
        elif tab == "Fitness Yearbook":
            years = sorted({m.split("-")[0] for m in months})
            cur_year = cur.split("-")[0]
            default_year_idx = years.index(cur_year) if cur_year in years else (len(years) - 1)
            _month_selector_label("Year")
            year_selected = st.selectbox("Year", years, index=default_year_idx, label_visibility="collapsed")
            month_selected = f"{year_selected}-01"
        else:
            month_selected = months[default_idx]

    st.markdown("<hr>", unsafe_allow_html=True)

    # Choose leaderboard month: always current month for the Leaderboard tab.
    lb_month = current_month_str() if tab == "Leaderboard" else month_selected

    users_result = get_users(lb_month)
    if not users_result.ok and users_result.status is GetUsersStatus.MISSING_MONTH_COLUMN:
        # Loud warning — the leaderboard would otherwise lie about who is
        # "In" for the month (adversarial P0-04).
        st.warning(users_result.message)
    elif not users_result.ok and users_result.status is GetUsersStatus.READ_ERROR:
        st.warning("Could not read the active-users roster. Showing workout-only standings.")

    lb_cutoff = winner_cutoff_for_month(lb_month)
    lb = month_leaderboard(
        df,
        lb_month,
        lb_cutoff,
        users_result.users if users_result.users else None,
    )

    df_month = df[(df["month"] == month_selected) & (df["workout_date"].notna())].copy()
    df_month_leaderboard = df[(df["month"] == lb_month) & (df["workout_date"].notna())].copy()

    if tab == "Leaderboard":
        _lazy_render("ui.leaderboard")(df=lb, df_month=df_month_leaderboard, month_str=lb_month, cutoff=lb_cutoff)
    elif tab == "Scorecard":
        _lazy_render("ui.scorecard")(lb=lb, df_month=df_month, cutoff=lb_cutoff)
    elif tab == "Fitness Yearbook":
        _lazy_render("ui.yearcalendar")(df=df, month_selected=month_selected)
    else:
        # Unknown tab — render the leaderboard as a safe default.
        _lazy_render("ui.leaderboard")(df=lb, df_month=df_month_leaderboard, month_str=lb_month, cutoff=lb_cutoff)

    # Data-quality drop-counts are debug-only. Hidden from end users on
    # the live site; surface only when explicitly opted-in via either
    # the APP_DEBUG=1 environment variable or `?debug=1` in the URL.
    quality_report = df.attrs.get("quality_report") if hasattr(df, "attrs") else None
    debug_env = os.getenv("APP_DEBUG", "").strip().lower() in {"1", "true", "yes"}
    debug_qs = str(st.query_params.get("debug", "")).strip().lower() in {"1", "true", "yes"}
    if (debug_env or debug_qs) and quality_report is not None and quality_report.total_dropped > 0:
        with st.expander("Data quality (rows dropped during cleaning)", expanded=False):
            st.json(quality_report.as_dict())


if __name__ == "__main__":
    main()
