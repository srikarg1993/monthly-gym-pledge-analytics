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
from globals import *


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
# Clean, modern LIGHT UI (no dark tables)
# =========================================================

def load_css(file_path: str):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles/theme.css")


# =========================================================
# Seaborn settings (as requested)
# =========================================================
def style_plots():
    sns.set_theme(style="darkgrid", palette="muted")
    mpl.rcParams["figure.dpi"] = 150
    plt.rcParams["font.family"] = "Roboto"


def set_title_labels(ax, title, xlabel="", ylabel=""):
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9, fontweight="bold")

def read_google_sheet_as_df(spreadsheet_id: str, worksheet_name: str) -> pd.DataFrame:
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)

    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)
    df = df.replace("", pd.NA).dropna(how="all")
    return df


# =========================================================
# Cleaning (matches your sheet headers)
# =========================================================
def normalize_bool(x) -> bool:
    if pd.isna(x):
        return False
    s = str(x).strip().lower()
    return s in {"yes", "true", "1", "y", "t"}


def clean(
    df: pd.DataFrame,
    *,
    col_timestamp: str = "Timestamp",
    col_name: str = "You are?",
    col_wkdate: str = "Workout date",
    col_250: str = "Burnt >= 250 calories?",
    dedupe: bool = True,
) -> pd.DataFrame:
    df = df.copy()

    expected = {col_timestamp, col_name, col_wkdate, col_250}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns: {missing}. Found columns: {list(df.columns)}"
        )

    df = df.rename(
        columns={
            col_timestamp: "timestamp",
            col_name: "name_raw",
            col_wkdate: "workout_date_raw",
            col_250: "burnt_250_raw",
        }
    )

    df["name"] = (
        df["name_raw"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["timestamp_date"] = df["timestamp"].dt.date

    df["workout_date"] = pd.to_datetime(df["workout_date_raw"], errors="coerce").dt.date
    df["burnt_250"] = df["burnt_250_raw"].apply(normalize_bool)

    if dedupe:
        df = (
            df.sort_values("timestamp", ascending=True)
            .drop_duplicates(subset=["name", "workout_date"], keep="last")
            .reset_index(drop=True)
        )

    df["any_workout"] = df["workout_date"].notna()
    df["workout_dt"] = pd.to_datetime(df["workout_date"], errors="coerce")
    df["month"] = df["workout_dt"].dt.to_period("M").astype(str)
    df["dow"] = df["workout_dt"].dt.day_name()
    df["dom"] = df["workout_dt"].dt.day

    df["log_delay_days"] = (
        pd.to_datetime(df["timestamp_date"], errors="coerce")
        - pd.to_datetime(df["workout_date"], errors="coerce")
    ).dt.days

    return df


# =========================================================
# Metrics
# =========================================================
def current_month_str() -> str:
    t = date.today()
    return f"{t.year:04d}-{t.month:02d}"


def month_bounds(month_str: str):
    y, m = map(int, month_str.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last_day)


def month_leaderboard(df: pd.DataFrame, month_str: str, cutoff: int, all_users=None) -> pd.DataFrame:
    d = df[(df["month"] == month_str) & (df["workout_date"].notna())].copy()


    any_days = d.groupby("name")["workout_date"].nunique().rename("workout_days").reset_index()
    qual_days = d[d["burnt_250"]].groupby("name")["workout_date"].nunique().rename("qualifying_days").reset_index()


    out = any_days.merge(qual_days, on="name", how="left")
    out["qualifying_days"] = out["qualifying_days"].fillna(0).astype(int)
    out["workout_days"] = out["workout_days"].fillna(0).astype(int)
    

    if all_users is not None:
        all_users_df = pd.DataFrame({"name": list(all_users)})
        out = all_users_df.merge(out, on="name", how="left").fillna(0)
        out["qualifying_days"] = out["qualifying_days"].astype(int)
        out["workout_days"] = out["workout_days"].astype(int)

    out["workouts_left"] = (cutoff - out["qualifying_days"]).clip(lower=0)
    out["is_winner"] = out["qualifying_days"] >= cutoff
    out["progress"] = (out["qualifying_days"] / max(cutoff, 1)).clip(0, 1)
    out["rank"] = (
        out["qualifying_days"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )


    out = out.sort_values(
        ["rank", "is_winner", "qualifying_days", "workout_days", "name"],
        ascending=[True, False, False, False, True],
    ).reset_index(drop=True)

    return out



def longest_streak(dates):
    if not dates:
        return 0
    ds = sorted(set(dates))
    best = cur = 1
    for i in range(1, len(ds)):
        if (ds[i] - ds[i - 1]).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best


def fastest_winner_date(df_month: pd.DataFrame, name: str, cutoff: int):
    d = df_month[(df_month["name"] == name) & (df_month["burnt_250"])].copy()
    if d.empty:
        return None
    days = sorted(set(d["workout_date"].dropna().tolist()))
    if len(days) < cutoff:
        return None
    return days[cutoff - 1]


def lazy_logger_score(df_month: pd.DataFrame):
    d = df_month.dropna(subset=["workout_date", "timestamp"]).copy()
    if d.empty:
        return None
    agg = (
        d.groupby("name")["log_delay_days"]
        .mean()
        .rename("avg_log_delay_days")
        .reset_index()
        .sort_values("avg_log_delay_days", ascending=False)
    )
    return agg


def frontload_vs_cram(df_month: pd.DataFrame):
    if df_month.empty:
        return pd.DataFrame()
    start, end = month_bounds(df_month["month"].iloc[0])
    mid = start + (end - start) / 2
    mid = date(mid.year, mid.month, int(mid.day))

    d = df_month[df_month["burnt_250"]].copy()

    def split_counts(x):
        days = sorted(set(x["workout_date"].dropna().tolist()))
        first = sum(1 for dd in days if dd <= mid)
        second = sum(1 for dd in days if dd > mid)
        total = first + second
        if total == 0:
            style = "No qualifying"
        elif first >= second + 3:
            style = "Front-loader"
        elif second >= first + 3:
            style = "Crammer"
        else:
            style = "Balanced"
        return pd.Series({"first_half": first, "second_half": second, "style": style})

    out = d.groupby("name").apply(split_counts).reset_index()
    return out.sort_values(["style", "first_half"], ascending=[True, False])


# =========================================================
# Sidebar navigation (buttons, no emojis)
# =========================================================
if "tab" not in st.session_state:
    st.session_state["tab"] = "Leaderboard"


with st.sidebar:
    if st.button("Leaderboard", use_container_width=True):
        st.session_state["tab"] = "Leaderboard"
    if st.button("Scorecard", use_container_width=True):
        st.session_state["tab"] = "Scorecard"
    if st.button("Personalization", use_container_width=True):
        st.session_state["tab"] = "Personalization"
    if st.button("Month-over-month Trends", use_container_width=True):
        st.session_state["tab"] = "Month-over-month Trends"

    dedupe = True


# =========================================================
# Load and clean
# =========================================================
try:
    raw = read_google_sheet_as_df(SPREADSHEET_ID, WORKSHEET_NAME)
except Exception as e:
    st.error("Could not read Google Sheet. Check: secrets/service_account.json and share the sheet with the service-account email.")
    st.exception(e)
    st.stop()

try:
    df = clean(raw, dedupe=dedupe)
except Exception as e:
    st.error("Data cleaning failed (header mismatch is most likely).")
    st.exception(e)
    st.stop()

months = sorted([m for m in df["month"].dropna().unique().tolist()])
if not months:
    st.warning("No workouts found yet.")
    st.stop()

cur = current_month_str()
default_idx = months.index(cur) if cur in months else (len(months) - 1)

# =========================================================
# Top header bar (tight + aligned)
# =========================================================

st.write("")

top = st.columns([1.2, 1.2, 1.1, 1.0], gap="medium")
with top[0]:
    month_selected = st.selectbox("Month", months, index=default_idx)
    
lb = month_leaderboard(df, month_selected, WINNER_CUTOFF, USERS)
df_month = df[(df["month"] == month_selected) & (df["workout_date"].notna())].copy()

tab = st.session_state["tab"]


# =========================================================
# Leaderboard
# =========================================================
if tab == "Leaderboard":
    left, right = st.columns([1.9, 1.0], gap="large")

    with left:
        st.subheader("Live Leaderboard")

        winners = lb[lb["is_winner"]]
        total_people = int(lb["name"].nunique())
        winner_count = int(winners["name"].nunique())

        st.markdown(
            f"""
<div class="kpiRow">
  <div class="kpi"><div class="label">Participants</div><div class="value">{total_people}</div></div>
  <div class="kpi"><div class="label">Winners</div><div class="value">{winner_count}</div></div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.write("")

        max_workouts = 16

        st.markdown("<div class='leaderboard'>", unsafe_allow_html=True)

        for _, row in lb.iterrows():
            progress = int((row["qualifying_days"] / max_workouts) * 100)
            winner_class = "winner" if row["is_winner"] else ""

            st.markdown(
                f"""
                <div class="lb-row {winner_class}">
                <div class="lb-rank">#{row['rank']}</div>
                <div class="lb-name">{row['name']}</div>
                <div class="lb-workouts">{row['qualifying_days']} workouts</div>

                <div class="lb-bar-wrap">
                    <div class="lb-bar" style="width:{progress}%"></div>
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)


    with right:

        st.subheader("Workouts left (by person)")

        people = sorted(lb["Name"].dropna().unique().tolist()) if "Name" in lb.columns else sorted(lb["name"].dropna().unique().tolist())
        who = st.selectbox("Select person", sorted(lb["name"].dropna().unique().tolist()))

        row = lb[lb["name"] == who].iloc[0]
        remaining = int(row["workouts_left"])
        qdays = int(row["qualifying_days"])
        wdays = int(row["workout_days"])


        st.markdown(f"### {who}")
        st.markdown("<div class='small-muted'>This month</div>", unsafe_allow_html=True)

        completed = qdays
        remaining = max(WINNER_CUTOFF - completed, 0)

        # ---- DONUT CHART ----
        fig, ax = plt.subplots()

        values = [(completed*100)/16, (remaining*100)/16]

        ax.pie(
            values,
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.2, edgecolor="none"),
        )

        # Center text
        ax.text(
            0, 0.05,
            f"{remaining}",
            ha="center",
            va="center",
            fontsize=30,
            fontweight="800",
            color="#E4E6EB",
        )

        ax.text(
            0, -0.18,
            "days left",
            ha="center",
            va="center",
            fontsize=15,
            color="#A0A4B3",
        )
        ax.axis("equal")

        st.pyplot(fig, transparent=True)

        # ---- STATUS ----
        if remaining == 0:
            st.success("Winner locked 🏆")
        else:
            st.info("Keep Going !")


# =========================================================
# Scorecard
# =========================================================
elif tab == "Scorecard":
    st.markdown("<hr>", unsafe_allow_html=True)

    winner_df = lb[lb["rank"] == 2].reset_index(drop=True)

    streak_rows = []
    for name, g in df_month[df_month["burnt_250"]].groupby("name"):
        streak_rows.append({"Name": name, "Longest Streak": longest_streak(g["workout_date"].dropna().tolist())})
    streak_df = pd.DataFrame(streak_rows).sort_values("Longest Streak", ascending=False)

    fw_rows = []
    for name in df_month["name"].dropna().unique():
        fw = fastest_winner_date(df_month, name, WINNER_CUTOFF)
        if fw:
            fw_rows.append({"Name": name, "Hit cutoff on": fw})
    fw_df = pd.DataFrame(fw_rows).sort_values("Hit cutoff on") if fw_rows else pd.DataFrame(columns=["Name","Hit cutoff on"])

    lazy_df = lazy_logger_score(df_month)
    fl = frontload_vs_cram(df_month)

    barely_missed = lb[(~lb["is_winner"]) & (lb["qualifying_days"].isin([WINNER_CUTOFF-2, WINNER_CUTOFF-1]))].copy()
    barely_missed = barely_missed.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    consistent_not_qual = lb[(~lb["is_winner"]) & (lb["workout_days"] >= WINNER_CUTOFF)].copy()
    consistent_not_qual = consistent_not_qual.rename(columns={"name":"Name","qualifying_days":"Qualifying Days","workouts_left":"Workouts Left","workout_days":"Workout Days"})

    st.markdown("### Winners!! ")
    for _, row in winner_df.iterrows():
        winner_class = "winner" if row["is_winner"] else ""

        st.markdown(
            f"""
            <div class="lb-row {winner_class}">
            <div class="lb-rank">#{row['rank']}</div>
            <div class="lb-name">{row['name']}</div>
            <div class="lb-workouts">{row['qualifying_days']} workouts</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<hr>", unsafe_allow_html=True)

    a, b, c = st.columns(3, gap="large")

    with a:

        with st.container():
            st.markdown("### Longest streak")

            if not streak_df.empty:
                top = streak_df.iloc[0]
                st.markdown(
                    f"**Leader:** {top['Name']} — **{int(top['Longest Streak'])} days**"
                )
                st.dataframe(
                    streak_df.head(12),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No qualifying streaks yet.")


        # st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        # st.markdown("### Longest streak")
        # if not streak_df.empty:
        #     top = streak_df.iloc[0]
        #     st.markdown(f"**Leader:** {top['Name']} — **{int(top['Longest Streak'])} days**")
        #     st.table(streak_df.head(12), hide_index=True, use_container_width=True)
        # else:
        #     st.caption("No qualifying streaks yet.")
        # st.markdown("</div>", unsafe_allow_html=True)

    with b:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Fastest winner")
        if not fw_df.empty:
            top = fw_df.iloc[0]
            st.markdown(f"**Fastest:** {top['Name']} — cutoff on **{top['Hit cutoff on']}**")
            st.dataframe(fw_df.head(12), hide_index=True, use_container_width=True)
        else:
            st.caption("No winners yet (or not enough qualifying days).")
        st.markdown("</div>", unsafe_allow_html=True)

    with c:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Lazy logger")
        if lazy_df is not None and not lazy_df.empty:
            lazy_show = lazy_df.rename(columns={"name":"Name"})
            st.markdown(f"**Most delayed:** {lazy_show.iloc[0]['Name']} — avg **{lazy_show.iloc[0]['avg_log_delay_days']:.2f} days**")
            st.dataframe(lazy_show.head(12), hide_index=True, use_container_width=True)
        else:
            st.caption("Need timestamps to score logging delay.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    left, right = st.columns([1.2, 1.0], gap="large")

    with left:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Front-loading vs cramming")
        if not fl.empty:
            st.dataframe(
                fl.rename(columns={"name":"Name","first_half":"First half","second_half":"Second half","style":"Style"}),
                hide_index=True,
                use_container_width=True
            )
            style_plots()
            fig, ax = plt.subplots(figsize=(7.2, 3.0))
            sns.countplot(data=fl, x="style", ax=ax)
            set_title_labels(ax, "Distribution of styles", "Style", "People")
            st.pyplot(fig, use_container_width=True)
        else:
            st.caption("Not enough data.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### Barely missed & consistent-but-not-qualifying")
        st.caption("Barely missed = cutoff-2 or cutoff-1 qualifying days (not a winner).")
        st.dataframe(barely_missed[["Name","Qualifying Days","Workouts Left","Workout Days"]], hide_index=True, use_container_width=True)
        st.caption("Consistent but not qualifying = workout days ≥ cutoff but qualifying < cutoff.")
        st.dataframe(consistent_not_qual[["Name","Qualifying Days","Workouts Left","Workout Days"]], hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)




# =========================================================
# Personalization
# =========================================================
elif tab == "Personalization":
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


# =========================================================
# Month-over-month Trends
# =========================================================
else:
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
