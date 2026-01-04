from __future__ import annotations

import streamlit as st
import pandas as pd

from config import APP, SHEET
from data.sheets import fetch_sheet_df
from data.cleaning import clean_sheet
from metrics.dates import current_month_str
from metrics.leaderboard import month_leaderboard

from pages.leaderboard_page import render as leaderboard_render
from pages.scorecard_page import render as scorecard_render
from pages.personalization_page import render as personalization_render
from pages.trends_page import render as trends_render


def load_css(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def inject_css():
    css = load_css("assets/styles.css")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=APP.cache_ttl_seconds, show_spinner=False)
def load_raw_sheet() -> pd.DataFrame:
    return fetch_sheet_df(
        spreadsheet_id=SHEET.spreadsheet_id,
        worksheet_name=SHEET.worksheet_name,
        service_account_json_path=SHEET.service_account_json_path,
        scopes=SHEET.scopes,
    )


def sidebar_nav() -> str:
    if "tab" not in st.session_state:
        st.session_state["tab"] = "Leaderboard"

    with st.sidebar:
        st.markdown("<div class='sidebar-title'>Gym Kitty</div>", unsafe_allow_html=True)
        st.markdown("<div class='navhint'>Choose a view</div>", unsafe_allow_html=True)

        if st.button("Leaderboard", use_container_width=True):
            st.session_state["tab"] = "Leaderboard"
        if st.button("Scorecard", use_container_width=True):
            st.session_state["tab"] = "Scorecard"
        if st.button("Personalization", use_container_width=True):
            st.session_state["tab"] = "Personalization"
        if st.button("Month-over-month Trends", use_container_width=True):
            st.session_state["tab"] = "Month-over-month Trends"

        st.markdown("---")
        st.markdown("### Settings")
        winner_cutoff = st.number_input("Winner cutoff (qualifying days)", 1, 31, APP.default_winner_cutoff, 1)
        dedupe = st.toggle("De-duplicate (keep latest per day)", value=True)

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Refresh data", use_container_width=True):
                st.cache_data.clear()
        with c2:
            st.caption(f"Cache: {APP.cache_ttl_seconds}s")

    return st.session_state["tab"], int(winner_cutoff), bool(dedupe)


def header_bar(*, worksheet_name: str, spreadsheet_id: str, winner_cutoff: int):
    st.markdown(
        """
<div class="cardSolid">
  <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:16px;">
    <div>
      <div style="font-size:1.8rem; font-weight:800; line-height:1.12;">Gym Kitty Dashboard</div>
      <div class="small-muted">Live leaderboard • scorecard insights • personalization • trends</div>
    </div>
    <div class="badge"><span class="dot"></span> Live from Google Sheets</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.write("")

    top = st.columns([1.2, 1.2, 1.1, 1.0], gap="medium")
    with top[1]:
        st.markdown(f"<span class='badge'>Sheet tab: {worksheet_name}</span>", unsafe_allow_html=True)
    with top[2]:
        st.markdown(f"<span class='badge'>Sheet: …{spreadsheet_id[-8:]}</span>", unsafe_allow_html=True)
    with top[3]:
        st.markdown(f"<span class='badge'>Cutoff: {winner_cutoff} days</span>", unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title=APP.page_title,
        page_icon=APP.page_icon,
        layout=APP.layout,
        initial_sidebar_state=APP.initial_sidebar_state,
    )
    inject_css()

    tab, winner_cutoff, dedupe = sidebar_nav()

    # Load + clean
    try:
        raw = load_raw_sheet()
    except Exception as e:
        st.error(
            "Could not read Google Sheet. Check: secrets/service_account.json and share the sheet with the service-account email."
        )
        st.exception(e)
        st.stop()

    try:
        df = clean_sheet(raw, dedupe=dedupe)
    except Exception as e:
        st.error("Data cleaning failed (header mismatch is most likely).")
        st.exception(e)
        st.stop()

    months = sorted([m for m in df["month"].dropna().unique().tolist()])
    if not months:
        st.warning("No workouts found yet.")
        st.stop()

    cur = current_month_str()
    default_idx = months.index(cur) if cur in months else (len(months) - 1)

    header_bar(worksheet_name=SHEET.worksheet_name, spreadsheet_id=SHEET.spreadsheet_id, winner_cutoff=winner_cutoff)

    # Month selector (kept here so all pages share it)
    month_selected = st.selectbox("Month", months, index=default_idx)

    lb = month_leaderboard(df, month_selected, winner_cutoff)
    df_month = df[(df["month"] == month_selected) & (df["workout_date"].notna())].copy()

    # Route
    if tab == "Leaderboard":
        leaderboard_render(lb=lb, df_month=df_month, winner_cutoff=winner_cutoff)
    elif tab == "Scorecard":
        scorecard_render(lb=lb, df_month=df_month, winner_cutoff=winner_cutoff)
    elif tab == "Personalization":
        personalization_render(df_month=df_month)
    else:
        trends_render(df_all=df, winner_cutoff=winner_cutoff)


if __name__ == "__main__":
    main()
