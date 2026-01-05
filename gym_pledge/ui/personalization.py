import pandas as pd
import matplotlib.pyplot as plt

from config.globals import *
from data.source import *
from data.metrics import *
from ui.common import *


def render(*, df_month) -> None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personalization")
    st.markdown("<div class='small-muted'>Day-of-week trends (overall vs selected person)</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    people = sorted(df_month["name"].dropna().unique().tolist())
    who = st.selectbox("Person", people)

    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    style_plots()
    overall = (
        df_month[df_month["any_workout"]]
        .groupby("dow")["workout_date"]
        .nunique()
        .reindex(weekday_order)
        .reset_index(name="Unique workout days")
    )

    person = (
        df_month[(df_month["name"] == who) & (df_month["any_workout"])]
        .groupby("dow")["workout_date"]
        .nunique()
        .reindex(weekday_order)
        .reset_index(name="Unique workout days")
    )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6.9, 3.2))
        sns.barplot(data=overall, x="dow", y="Unique workout days", ax=ax)
        set_title_labels(ax, "Overall workouts by weekday", "Weekday", "Unique days")
        ax.tick_params(axis="x", labelrotation=18)
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6.9, 3.2))
        sns.barplot(data=person, x="dow", y="Unique workout days", ax=ax)
        set_title_labels(ax, f"{who}: workouts by weekday", "Weekday", "Unique days")
        ax.tick_params(axis="x", labelrotation=18)
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)