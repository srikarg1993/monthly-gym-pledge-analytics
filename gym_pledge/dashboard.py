from pathlib import Path

import streamlit as st

from app_time import current_month_str
from config.globals import winner_cutoff_for_month
from data.metrics import month_leaderboard
from data.source import get_data, get_users
from ui.about import render as render_about
from ui.leaderboard import render as render_leaderboard
from ui.logyourworkout import render as render_logyourworkout
from ui.monthovermonth import render as render_monthovermonth
from ui.personalization import render as render_personalization
from ui.scorecard import render as render_scorecard
from ui.yearcalendar import render as render_yearcalendar

# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="Monthly Gym Pledge",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# Load CSS
# =========================================================


def load_css(rel_path: str):
    css_path = Path(__file__).resolve().parent / rel_path
    st.markdown(
        f"<style>{css_path.read_text()}</style>",
        unsafe_allow_html=True,
    )


load_css("styles/theme.css")


def inject_sidebar_autocollapse() -> None:
    st.markdown(
        """
        <script>
        (function() {
          const parentDoc = window.parent.document;
          const MOBILE_WIDTH = 768;

          function collapseSidebarIfMobile() {
            if (window.innerWidth > MOBILE_WIDTH) return;
            const collapseButton = parentDoc.querySelector('button[title="Collapse sidebar"]') ||
              parentDoc.querySelector('[data-testid="collapsedControl"]');
            if (collapseButton) collapseButton.click();
          }

          function attachHandlers() {
            const sidebar = parentDoc.querySelector('section[data-testid="stSidebar"]');
            if (!sidebar) return;
            const buttons = sidebar.querySelectorAll('button');
            buttons.forEach((btn) => {
              if (btn.dataset.sidebarAutocollapse) return;
              btn.dataset.sidebarAutocollapse = '1';
              btn.addEventListener('click', () => {
                setTimeout(collapseSidebarIfMobile, 50);
              });
            });
          }

          attachHandlers();
          const observer = new MutationObserver(() => attachHandlers());
          observer.observe(parentDoc.body, { childList: true, subtree: true });
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Sidebar navigation (buttons, no emojis)
# =========================================================
if "tab" not in st.session_state:
    st.session_state["tab"] = "Leaderboard"


with st.sidebar:
    if st.button("About us", use_container_width=True):
        st.session_state["tab"] = "About us"
    if st.button("Leaderboard", use_container_width=True):
        st.session_state["tab"] = "Leaderboard"
    if st.button("Scorecard", use_container_width=True):
        st.session_state["tab"] = "Scorecard"
    if st.button("Fitness Yearbook", use_container_width=True):
        st.session_state["tab"] = "Fitness Yearbook"
    if st.button("Log Your Workout", use_container_width=True):
        st.session_state["tab"] = "Log Your Workout!"

    dedupe = True


inject_sidebar_autocollapse()

# =========================================================
# Get data
# =========================================================
df = get_data()

months = sorted([m for m in df["month"].dropna().unique().tolist()])
if not months:
    st.warning("No workouts found yet.")
    st.stop()

cur = current_month_str()
default_idx = months.index(cur) if cur in months else (len(months) - 1)

header_cols = st.columns([1, 0.28], gap="large")
with header_cols[0]:
    st.markdown("# Monthly Pledge to Fitness ")
with header_cols[1]:
    # Hide month selector on pages where it isn't needed (Leaderboard and Log Your Workout)
    current_tab = st.session_state.get("tab", "")
    if (
        ("Log Your Workout" not in current_tab)
        and (current_tab != "Leaderboard")
        and (current_tab != "About us")
        and (current_tab != "Month-over-month Trends")
        and (current_tab != "Fitness Yearbook")
    ):
        st.markdown(
            "<div style='white-space:nowrap; font-size:18px; font-weight:600'>Month</div>", unsafe_allow_html=True
        )
        month_selected = st.selectbox("", months, index=default_idx, label_visibility="collapsed")
    else:
        month_selected = months[default_idx]

st.markdown("<hr>", unsafe_allow_html=True)

# Choose leaderboard month: always use current month for the Leaderboard tab
tab = st.session_state.get("tab", "Leaderboard")
lb_month = current_month_str() if tab == "Leaderboard" else month_selected

users = get_users(lb_month)
lb_cutoff = winner_cutoff_for_month(lb_month)
lb = month_leaderboard(df, lb_month, lb_cutoff, users or None)
# df_month represents the selected month for other pages (Scorecard etc.)
df_month = df[(df["month"] == month_selected) & (df["workout_date"].notna())].copy()
df_month_leaderboard = df[(df["month"] == lb_month) & (df["workout_date"].notna())].copy()


# =========================================================
# UI components
# =========================================================

if tab == "Leaderboard":
    render_leaderboard(df=lb, df_month=df_month_leaderboard, month_str=lb_month, cutoff=lb_cutoff)
elif tab == "Scorecard":
    render_scorecard(lb=lb, df_month=df_month, cutoff=lb_cutoff)
elif tab == "Personalization":
    render_personalization(df_month=df_month)
elif tab == "Fitness Yearbook":
    render_yearcalendar(df=df, month_selected=month_selected)
elif tab == "Month-over-month Trends":
    render_monthovermonth(df=df)
elif tab == "About us":
    render_about()
else:
    render_logyourworkout()
