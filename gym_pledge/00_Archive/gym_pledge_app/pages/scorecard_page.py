from __future__ import annotations

import pandas as pd
import streamlit as st

from metrics.scorecard import (
    fastest_winner_date,
    frontload_vs_cram,
    lazy_logger_score,
    longest_streak,
)
from viz.charts import count_styles


def render(*, lb: pd.DataFrame, df_month: pd.DataFrame, winner_cutoff: int):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Scorecard")
    st.markdown(
        "<div class='small-muted'>Longest streak • fastest winner • lazy logger • front-loading vs cramming • barely missed</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    streak_rows = []
    for name, g in df_month[df_month["burnt_250"]].groupby("name"):
        streak_rows.append({"Name": name, "Longest Streak": longest_streak(g["workout_date"].dropna().tolist())})
    streak_df = pd.DataFrame(streak_rows).sort_values("Longest Streak", ascending=False)

    fw_rows = []
    for name in df_month["name"].dropna().unique():
        fw = fastest_winner_date(df_month, name, winner_cutoff)
        if fw:
            fw_rows.append({"Name": name, "Hit cutoff on": fw})
    fw_df = pd.DataFrame(fw_rows).sort_values("Hit cutoff on") if fw_rows else pd.DataFrame(columns=["Name","Hit cutoff on"])

    lazy_df = lazy_logger_score(df_month)
    fl = frontload_vs_cram(df_month)

    barely_missed = lb[(~lb["is_winner"]) & (lb["qualifying_days"].isin([winner_cutoff-2, winner_cutoff-1]))].copy()
    barely_missed = barely_missed.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    consistent_not_qual = lb[(~lb["is_winner"]) & (lb["workout_days"] >= winner_cutoff)].copy()
    consistent_not_qual = consistent_not_qual.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    a, b, c = st.columns(3, gap="large")

    with a:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Longest streak")
        if not streak_df.empty:
            top = streak_df.iloc[0]
            st.markdown(f"**Leader:** {top['Name']} — **{int(top['Longest Streak'])} days**")
            st.dataframe(streak_df.head(12), hide_index=True, use_container_width=True)
        else:
            st.caption("No qualifying streaks yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with b:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Fastest winner")
        if not fw_df.empty:
            top = fw_df.iloc[0]
            st.markdown(f"**Fastest:** {top['Name']} — cutoff on **{top['Hit cutoff on']}**")
            st.dataframe(fw_df.head(12), hide_index=True, use_container_width=True)
        else:
            st.caption("No winners yet (or not enough qualifying days).")
        st.markdown("</div>", unsafe_allow_html=True)

    with c:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Lazy logger")
        if lazy_df is not None and not lazy_df.empty:
            lazy_show = lazy_df.rename(columns={"name":"Name"})
            st.markdown(
                f"**Most delayed:** {lazy_show.iloc[0]['Name']} — avg **{lazy_show.iloc[0]['avg_log_delay_days']:.2f} days**"
            )
            st.dataframe(lazy_show.head(12), hide_index=True, use_container_width=True)
        else:
            st.caption("Need timestamps to score logging delay.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1.0], gap="large")

    with left:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Front-loading vs cramming")
        if not fl.empty:
            st.dataframe(
                fl.rename(columns={"name":"Name","first_half":"First half","second_half":"Second half","style":"Style"}),
                hide_index=True,
                use_container_width=True
            )
            fig = count_styles(fl)
            st.pyplot(fig, use_container_width=True)
        else:
            st.caption("Not enough data.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Barely missed & consistent-but-not-qualifying")
        st.caption("Barely missed = cutoff-2 or cutoff-1 qualifying days (not a winner).")
        st.dataframe(barely_missed[["Name","Qualifying Days","Workouts Left","Workout Days"]], hide_index=True, use_container_width=True)
        st.caption("Consistent but not qualifying = workout days ≥ cutoff but qualifying < cutoff.")
        st.dataframe(consistent_not_qual[["Name","Qualifying Days","Workouts Left","Workout Days"]], hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
