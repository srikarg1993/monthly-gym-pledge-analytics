from __future__ import annotations

import pandas as pd
import streamlit as st

from metrics.trends import build_month_over_month
from viz.charts import line_mom


def render(*, df_all: pd.DataFrame, winner_cutoff: int):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Month-over-month Trends")
    st.markdown("<div class='small-muted'>Participation, winners, and qualifying intensity over time</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    mom = build_month_over_month(df_all, winner_cutoff)

    st.dataframe(mom, hide_index=True, use_container_width=True)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.pyplot(line_mom(mom, "Participants", "Participants per month", "Participants"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.pyplot(line_mom(mom, "Winners", "Winners per month", "Winners"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.pyplot(
            line_mom(mom, "Avg qualifying days / person", "Avg qualifying intensity", "Avg qualifying days"),
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
