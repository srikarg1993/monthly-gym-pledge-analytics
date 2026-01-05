import calendar
from datetime import date
import numpy as np
import pandas as pd
import streamlit as st

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

import gspread
from google.oauth2.service_account import Credentials
from config.globals import *
from data.source import *
from data.metrics import *
from ui.leaderboard import render as render_leaderboard
from ui.scorecard import render as render_scorecard
from ui.personalization import render as render_personalization
from ui.monthovermonth import render as render_monthovermonth
from ui.logyourworkout import render as render_logyourworkout


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

def load_css(file_path: str):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles/theme.css")

def current_month_str() -> str:
    t = date.today()
    return f"{t.year:04d}-{t.month:02d}"

# =========================================================
# Sidebar navigation (buttons, no emojis)
# =========================================================
if "tab" not in st.session_state:
    st.session_state["tab"] = "Leaderboard"


with st.sidebar:
    if st.button("Leaderboard", use_container_width=True):
        st.session_state["tab"] = "Leaderboard"
    # if st.button("Scorecard", use_container_width=True):
    #     st.session_state["tab"] = "Scorecard"
    # if st.button("Personalization", use_container_width=True):
    #     st.session_state["tab"] = "Personalization"
    # if st.button("Month-over-month Trends", use_container_width=True):
    #     st.session_state["tab"] = "Month-over-month Trends"
    if st.button("Log Your Workout", use_container_width=True):
        st.session_state["tab"] = "Log Your Workout!"

    dedupe = True


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

st.write("")
st.write("")
st.markdown("# Monthly Pledge to Fitness ")
st.markdown("<hr>", unsafe_allow_html=True)
top = st.columns([1.2, 1.2, 1.1, 1.0], gap="medium")
with top[0]:
    month_selected = st.selectbox("Month", months, index=default_idx)

lb = month_leaderboard(df, month_selected, WINNER_CUTOFF, USERS)
df_month = df[(df["month"] == month_selected) & (df["workout_date"].notna())].copy()

tab = st.session_state["tab"]


# =========================================================
# UI components
# =========================================================

if tab == "Leaderboard":
    render_leaderboard(df = lb)
elif tab == "Scorecard":
    render_scorecard(lb = lb, df_month = df_month)
elif tab == "Personalization":
    render_personalization( df_month = df_month)
elif tab == "Month-over-month Trends":
    render_monthovermonth( df = df)
else :
    render_logyourworkout()

    
    