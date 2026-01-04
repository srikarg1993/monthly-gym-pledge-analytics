from __future__ import annotations

import numpy as np
import streamlit as st
import pandas as pd

from viz.charts import bar_qualifying_by_dom


def render(*, lb: pd.DataFrame, df_month: pd.DataFrame, winner_cutoff: int):
    left, right = st.columns([1.9, 1.0], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Live Leaderboard")

        winners = lb[lb["is_winner"]]
        total_people = int(lb["name"].nunique())
        winner_count = int(winners["name"].nunique())
        total_qual = int(lb["qualifying_days"].sum())

        st.markdown(
            f"""
<div class="kpiRow">
  <div class="kpi"><div class="label">Participants</div><div class="value">{total_people}</div></div>
  <div class="kpi"><div class="label">Winners</div><div class="value">{winner_count}</div></div>
  <div class="kpi"><div class="label">Total qualifying days</div><div class="value">{total_qual}</div></div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.write("")

        show = lb.copy()
        show.insert(0, "Status", np.where(show["is_winner"], "Winner", ""))
        show = show.rename(
            columns={
                "name": "Name",
                "qualifying_days": "Qualifying Days",
                "workouts_left": "Workouts Left",
                "workout_days": "Workout Days",
                "progress": "Progress",
            }
        )

        st.dataframe(
            show[["Status", "Name", "Qualifying Days", "Workouts Left", "Workout Days", "Progress"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Progress": st.column_config.ProgressColumn(
                    "Progress",
                    min_value=0.0,
                    max_value=1.0,
                    format="%.0f%%",
                    help="Qualifying progress toward cutoff",
                )
            },
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Workouts left (by person)")

        who = st.selectbox("Select person", sorted(lb["name"].dropna().unique().tolist()))
        row = lb[lb["name"] == who].iloc[0]
        remaining = int(row["workouts_left"])
        qdays = int(row["qualifying_days"])
        wdays = int(row["workout_days"])

        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown(f"### {who}")
        st.markdown("<div class='small-muted'>This month</div>", unsafe_allow_html=True)
        st.markdown(f"- Qualifying: **{qdays} / {winner_cutoff}**")
        st.markdown(f"- Workout days (any): **{wdays}**")
        st.markdown(f"#### Remaining: **{remaining}**")
        if remaining == 0:
            st.success("Winner locked")
        else:
            st.info("Keep going")
        st.markdown("</div>", unsafe_allow_html=True)

        fig = bar_qualifying_by_dom(df_month, who)
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.caption("No qualifying workouts yet for this person.")
        st.markdown("</div>", unsafe_allow_html=True)
