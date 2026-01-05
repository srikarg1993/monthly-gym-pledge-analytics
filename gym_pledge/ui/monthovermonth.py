import pandas as pd
import matplotlib.pyplot as plt

from config.globals import *
from data.source import *
from data.metrics import *
from ui.common import *


def render(*, df) -> None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Month-over-month Trends")
    st.markdown("<div class='small-muted'>Participation, winners, and qualifying intensity over time</div>", unsafe_allow_html=True)
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

    style_plots()
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        sns.lineplot(data=mom, x="month", y="Participants", marker="o", ax=ax)
        set_title_labels(ax, "Participants per month", "Month", "Participants")
        ax.tick_params(axis="x", labelrotation=18)
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        sns.lineplot(data=mom, x="month", y="Winners", marker="o", ax=ax)
        set_title_labels(ax, "Winners per month", "Month", "Winners")
        ax.tick_params(axis="x", labelrotation=18)
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        sns.lineplot(data=mom, x="month", y="Avg qualifying days / person", marker="o", ax=ax)
        set_title_labels(ax, "Avg qualifying intensity", "Month", "Avg qualifying days")
        ax.tick_params(axis="x", labelrotation=18)
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
