"""Personalization page: per-person day-of-week trends and comparison charts."""

import streamlit as st

from ui.common import render_card_end, render_card_start, render_seaborn_line, style_plots


def render(*, df_month) -> None:
    render_card_start(title="Personalization", subtitle="Day-of-week trends (overall vs selected person)")
    st.markdown("<hr>", unsafe_allow_html=True)

    people = sorted(df_month["name"].dropna().unique().tolist())
    who = st.selectbox("Person", people)

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

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
        render_card_start()
        fig = render_seaborn_line(
            overall,
            x="dow",
            y="Unique workout days",
            title="Overall workouts by weekday",
            xlabel="Weekday",
            ylabel="Unique days",
            figsize=(6.9, 3.2),
        )
        st.pyplot(fig, use_container_width=True)
        render_card_end()

    with right:
        render_card_start()
        fig = render_seaborn_line(
            person,
            x="dow",
            y="Unique workout days",
            title=f"{who}: workouts by weekday",
            xlabel="Weekday",
            ylabel="Unique days",
            figsize=(6.9, 3.2),
        )
        st.pyplot(fig, use_container_width=True)
        render_card_end()

    render_card_end()
