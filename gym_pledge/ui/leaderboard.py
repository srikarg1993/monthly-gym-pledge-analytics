import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime


from config.globals import WINNER_CUTOFF
from data.source import *     
from data.metrics import *     


def _name_col(df):
    """Return the canonical name column."""
    return "name" if "name" in df.columns else "Name"


def _render_kpis(lb, name_col: str) -> None:
    winners = lb[lb["is_winner"]]
    total_people = int(lb[name_col].nunique())
    winner_count = int(winners[name_col].nunique())
    month_year = datetime.now().strftime("%b %Y")

    st.markdown(
        f"""
        <div class="kpiRow">
          <div class="kpi">
            <div class="label">Participants</div>
            <div class="value">{total_people}</div>
          </div>
          <div class="kpi">
            <div class="label">Winners</div>
            <div class="value">{winner_count}</div>
          </div>
          <div class="kpi">
            <div class="label">Month</div>
            <div class="value">{month_year}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def _render_leaderboard_rows(lb, *, name_col: str, max_workouts: int) -> None:
    st.markdown("<div class='leaderboard'>", unsafe_allow_html=True)

    for _, row in lb.iterrows():
        qdays = int(row.get("qualifying_days", 0))
        progress = int((qdays / max_workouts) * 100) if max_workouts else 0
        progress = max(0, min(progress, 100))

        winner_class = "winner" if bool(row.get("is_winner", False)) else ""
        rank = row.get("rank", "")
        name = row.get(name_col, "")

        st.markdown(
            f"""
            <div class="lb-row {winner_class}">
              <div class="lb-rank">#{rank}</div>
              <div class="lb-name">{name}</div>
              <div class="lb-workouts">{qdays} workouts</div>
              <div class="lb-bar-wrap">
                <div class="lb-bar" style="width:{progress}%"></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _donut_days_left(completed: int, cutoff: int) -> None:
    remaining = max(cutoff - completed, 0)

    fig, ax = plt.subplots()
    ax.pie(
        [completed, remaining],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.2, edgecolor="none"),
    )

    ax.text(
        0,
        0.05,
        f"{remaining}",
        ha="center",
        va="center",
        fontsize=30,
        fontweight="800",
        color="#E4E6EB",
    )
    ax.text(
        0,
        -0.18,
        "days left",
        ha="center",
        va="center",
        fontsize=15,
        color="#A0A4B3",
    )
    ax.axis("equal")

    st.pyplot(fig, transparent=True)

    if remaining == 0:
        st.success("Winner locked 🏆")
    else:
        st.info("Keep going!")


def render(*, df) -> None:
    lb = df.copy()
    name_col = _name_col(lb)

    left, right = st.columns([1.9, 1.0], gap="large")

    # ---------------- LEFT: Leaderboard ----------------
    with left:
        st.subheader("Live Leaderboard")
        _render_kpis(lb, name_col)

        max_workouts = WINNER_CUTOFF  # use constant instead of hardcoding 16
        _render_leaderboard_rows(lb, name_col=name_col, max_workouts=max_workouts)

    # ---------------- RIGHT: Person detail ----------------
    with right:
        st.subheader("Workouts left (by person)")

        people = sorted(lb[name_col].dropna().unique().tolist())
        if not people:
            st.warning("No participants found.")
            return

        who = st.selectbox("Select person", people)

        selected = lb[lb[name_col] == who]
        if selected.empty:
            st.warning("No data found for selected person.")
            return

        row = selected.iloc[0]
        qdays = int(row.get("qualifying_days", 0))
        # wdays = int(row.get("workout_days", 0))         # keep if you use it
        # workouts_left = int(row.get("workouts_left", 0)) # keep if you use it

        st.markdown(f"### {who}")
        st.markdown("<div class='small-muted'>This month</div>", unsafe_allow_html=True)

        _donut_days_left(completed=qdays, cutoff=WINNER_CUTOFF)
