from __future__ import annotations

import pandas as pd
import streamlit as st

from viz.charts import bar_weekday


def render(*, df_month: pd.DataFrame):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personalization")
    st.markdown("<div class='small-muted'>Day-of-week trends (overall vs selected person)</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    people = sorted(df_month["name"].dropna().unique().tolist())
    who = st.selectbox("Person", people)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig = bar_weekday(df_month, name=None, title="Overall workouts by weekday")
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig = bar_weekday(df_month, name=who, title=f"{who}: workouts by weekday")
        st.pyplot(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
