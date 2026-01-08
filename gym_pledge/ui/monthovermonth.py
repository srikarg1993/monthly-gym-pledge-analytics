"""Month-over-month trends page: participation, winners, and intensity over time."""

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import seaborn as sns

from config.globals import WINNER_CUTOFF
from ui.common import style_plots, set_title_labels, render_seaborn_line, render_card_start, render_card_end


def render(*, df) -> None:
    render_card_start(title="Month-over-month Trends", subtitle="Participation, winners, and qualifying intensity over time")
    st.markdown("<hr>", unsafe_allow_html=True)

    participants = df[df["any_workout"]].groupby("month")["name"].nunique().reset_index(name="Participants")
    total_workouts = df[df["any_workout"]].groupby("month")["workout_date"].nunique().reset_index(name="Total unique workout days")

    qual = (
        df[df["burnt_250"]]
        .groupby(["month", "name"])["workout_date"]
        .nunique()
        .reset_index(name="qualifying_days")
    )
    avg_qual = qual.groupby("month")["qualifying_days"].mean().reset_index(name="Avg qualifying days / person")

    winners = qual.copy()
    winners["is_winner"] = winners["qualifying_days"] >= WINNER_CUTOFF
    winner_count = winners[winners["is_winner"]].groupby("month")["name"].nunique().reset_index(name="Winners")

    mom = (
        participants.merge(total_workouts, on="month", how="left")
        .merge(avg_qual, on="month", how="left")
        .merge(winner_count, on="month", how="left")
        .fillna({"Winners": 0, "Avg qualifying days / person": 0})
        .sort_values("month")
        .reset_index(drop=True)
    )

    st.dataframe(mom, hide_index=True, use_container_width=True)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        render_card_start()
        fig = render_seaborn_line(mom, x="month", y="Participants", title="Participants per month", xlabel="Month", ylabel="Participants")
        st.pyplot(fig, use_container_width=True)
        render_card_end()

        render_card_start()
        fig = render_seaborn_line(mom, x="month", y="Winners", title="Winners per month", xlabel="Month", ylabel="Winners")
        st.pyplot(fig, use_container_width=True)
        render_card_end()

    with c2:
        render_card_start()
        fig = render_seaborn_line(mom, x="month", y="Avg qualifying days / person", title="Avg qualifying intensity", xlabel="Month", ylabel="Avg qualifying days")
        st.pyplot(fig, use_container_width=True)
        render_card_end()

    render_card_end()
