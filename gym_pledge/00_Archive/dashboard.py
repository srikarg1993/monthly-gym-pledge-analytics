import calendar
from datetime import date
import numpy as np
import pandas as pd
import streamlit as st

import matplotlib.pyplot as plt
import seaborn as sns

import gspread
from google.oauth2.service_account import Credentials


# =========================
# App Config
# =========================
st.set_page_config(
    page_title="Gym Kitty",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# Premium light CSS
# =========================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

:root{
  --bg: #f7f8fb;
  --card: rgba(255,255,255,0.78);
  --card2: rgba(255,255,255,0.92);
  --text: #0b1220;
  --muted: rgba(11,18,32,0.60);
  --border: rgba(11,18,32,0.10);
  --shadow: 0 10px 30px rgba(11,18,32,0.08);
  --shadow2: 0 6px 18px rgba(11,18,32,0.08);
  --radius: 18px;
}

html, body, [class*="css"]{
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important;
  color: var(--text);
}

.stApp{
  background: radial-gradient(1200px 600px at 10% -10%, rgba(99,102,241,0.16), transparent 50%),
              radial-gradient(1200px 600px at 90% -10%, rgba(16,185,129,0.14), transparent 55%),
              var(--bg);
}

.block-container{
  padding-top: 1.1rem;
  padding-bottom: 2.0rem;
}

h1,h2,h3{ letter-spacing:-0.02em; }
.small-muted{ color: var(--muted); font-size: 0.95rem; }

.card{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow2);
  padding: 18px 18px;
}

.cardSolid{
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 18px 18px;
}

.kpiRow{ display:flex; gap:12px; flex-wrap:wrap; }
.kpi{
  flex:1;
  min-width: 180px;
  background: var(--card2);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow2);
  padding: 14px 14px;
}
.kpi .label{ font-size: 0.86rem; color: var(--muted); }
.kpi .value{ font-size: 1.65rem; font-weight: 800; margin-top: 4px; }

.badge{
  display:inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.65);
  font-size: 0.85rem;
  color: var(--muted);
}

hr{
  border: none;
  border-top: 1px solid var(--border);
  margin: 16px 0;
}

/* sidebar polish */
section[data-testid="stSidebar"]{
  background: rgba(255,255,255,0.55);
  border-right: 1px solid var(--border);
  backdrop-filter: blur(8px);
}
section[data-testid="stSidebar"] *{
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif !important;
}

/* dataframe */
div[data-testid="stDataFrame"]{
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow2);
}

/* buttons */
.stButton>button{
  border-radius: 12px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.9);
  box-shadow: var(--shadow2);
}
.stButton>button:hover{
  transform: translateY(-1px);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =========================
# Plot styling
# =========================
def style_plots():
    sns.set_theme(style="whitegrid")
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["font.family"] = "Inter"


def set_title_labels(ax, title, xlabel="", ylabel=""):
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=9, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=9, fontweight="bold")


# =========================
# Google Sheets read (from your notebook)
# =========================
SPREADSHEET_ID = "17RADj_LH-Lj_lB8QFZyxjv8iKFerNZfNT-7wmtPNuzk"
WORKSHEET_NAME = "Form Responses"
SERVICE_ACCOUNT_JSON_PATH = "secrets/service_account.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

@st.cache_data(ttl=60, show_spinner=False)
def read_google_sheet_as_df(spreadsheet_id: str, worksheet_name: str, json_path: str) -> pd.DataFrame:
    creds = Credentials.from_service_account_file(json_path, scopes=SCOPES)
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


# =========================
# Data normalize
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # You can tweak these once we inspect your exact sheet headers
    rename_map = {
        "timestamp": "timestamp",
        "time_stamp": "timestamp",
        "submitted_at": "timestamp",
        "name": "name",
        "full_name": "name",
        "date": "workout_date",
        "workout_date": "workout_date",
        "calories": "calories",
        "calories_burned": "calories",
        "burnt_250": "burnt_250",
        "qualifying": "burnt_250",
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df = df.rename(columns={k: v})

    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    if "workout_date" in df.columns:
        df["workout_date"] = pd.to_datetime(df["workout_date"], errors="coerce").dt.date

    if "burnt_250" not in df.columns:
        if "calories" in df.columns:
            df["calories"] = pd.to_numeric(df["calories"], errors="coerce")
            df["burnt_250"] = df["calories"] >= 250
        else:
            df["burnt_250"] = False
    else:
        # if sheet stores booleans as strings
        df["burnt_250"] = df["burnt_250"].astype(str).str.lower().isin(["true","1","yes","y"])

    df["any_workout"] = df["workout_date"].notna()

    if df["workout_date"].notna().any():
        dt = pd.to_datetime(df["workout_date"], errors="coerce")
        df["month"] = dt.dt.to_period("M").astype(str)
        df["dow"] = dt.dt.day_name()

    return df


# =========================
# Metrics helpers
# =========================
def current_month_str() -> str:
    t = date.today()
    return f"{t.year:04d}-{t.month:02d}"

def month_bounds(month_str: str):
    y, m = map(int, month_str.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, 1), date(y, m, last_day)

def month_leaderboard(df: pd.DataFrame, month_str: str, cutoff: int) -> pd.DataFrame:
    d = df[(df["month"] == month_str) & (df["workout_date"].notna())].copy()

    any_days = d.groupby("name")["workout_date"].nunique().rename("workout_days").reset_index()
    qual_days = d[d["burnt_250"]].groupby("name")["workout_date"].nunique().rename("qualifying_days").reset_index()

    out = any_days.merge(qual_days, on="name", how="left")
    out["qualifying_days"] = out["qualifying_days"].fillna(0).astype(int)
    out["workout_days"] = out["workout_days"].fillna(0).astype(int)
    out["workouts_left"] = (cutoff - out["qualifying_days"]).clip(lower=0).astype(int)
    out["is_winner"] = out["qualifying_days"] >= cutoff
    out["progress"] = (out["qualifying_days"] / max(cutoff, 1)).clip(0, 1)

    out = out.sort_values(["is_winner","qualifying_days","workout_days"], ascending=[False, False, False])
    return out

def longest_streak(dates: list[date]) -> int:
    if not dates:
        return 0
    ds = sorted(set(dates))
    best = cur = 1
    for i in range(1, len(ds)):
        if (ds[i] - ds[i-1]).days == 1:
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
    if "timestamp" not in df_month.columns:
        return None
    d = df_month.dropna(subset=["workout_date", "timestamp"]).copy()
    if d.empty:
        return None
    d["log_delay_days"] = (pd.to_datetime(d["timestamp"]).dt.date - d["workout_date"]).apply(lambda x: x.days if pd.notna(x) else np.nan)
    agg = d.groupby("name")["log_delay_days"].mean().rename("avg_log_delay_days").reset_index()
    return agg.sort_values("avg_log_delay_days", ascending=False)

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
    return out.sort_values(["style","first_half"], ascending=[True, False])


# =========================
# Header
# =========================
st.markdown(
    """
<div class="cardSolid">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:16px;">
    <div>
      <div style="font-size:1.65rem; font-weight:800;">Gym Kitty Dashboard</div>
      <div class="small-muted">Live leaderboard • behavior scorecards • personalization • month-over-month trends</div>
    </div>
    <div class="badge">Light • Minimal • Live from Google Sheets</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")

# =========================
# Sidebar nav ("tabs")
# =========================
with st.sidebar:
    st.markdown("### Tabs")
    tab = st.radio(
        "Tabs",
        ["Leaderboard", "Scorecard", "Personalization", "Month-over-month Trends"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Settings")
    WINNER_CUTOFF = st.number_input("Winner cutoff (qualifying days)", 1, 31, 16, 1)
    AUTO_REFRESH = st.toggle("Auto-refresh (60s)", value=True)

    st.markdown("---")
    cA, cB = st.columns(2)
    with cA:
        if st.button("Refresh now", use_container_width=True):
            st.cache_data.clear()
    with cB:
        st.caption("")


# =========================
# Load Data
# =========================
try:
    raw = read_google_sheet_as_df(SPREADSHEET_ID, WORKSHEET_NAME, SERVICE_ACCOUNT_JSON_PATH)
except Exception as e:
    st.error("Could not read Google Sheet. Check service account file path + sheet sharing permissions.")
    st.exception(e)
    st.stop()

df = normalize_columns(raw)

required = {"name", "workout_date"}
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Missing required columns after normalization: {missing}.")
    st.stop()

months = sorted([m for m in df.get("month", pd.Series([])).dropna().unique().tolist()])
if not months:
    st.warning("No workouts found yet.")
    st.stop()

cur_month = current_month_str()
default_idx = months.index(cur_month) if cur_month in months else len(months) - 1

top_bar = st.columns([1.2, 1, 1, 0.8])
with top_bar[0]:
    month_selected = st.selectbox("Month", months, index=default_idx)
with top_bar[1]:
    st.caption("")
    st.write("")
    st.markdown(f"<span class='badge'>Sheet Tab: {WORKSHEET_NAME}</span>", unsafe_allow_html=True)
with top_bar[2]:
    st.caption("")
    st.write("")
    st.markdown(f"<span class='badge'>Spreadsheet ID: …{SPREADSHEET_ID[-8:]}</span>", unsafe_allow_html=True)
with top_bar[3]:
    if AUTO_REFRESH:
        # Streamlit reruns on interaction; TTL cache handles freshness.
        st.markdown("<span class='badge'>Auto-refresh ON</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='badge'>Auto-refresh OFF</span>", unsafe_allow_html=True)

lb = month_leaderboard(df, month_selected, WINNER_CUTOFF)
df_month = df[(df["month"] == month_selected) & (df["workout_date"].notna())].copy()


# =========================
# Leaderboard
# =========================
if tab == "Leaderboard":
    left, right = st.columns([1.75, 1], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Live Leaderboard")

        winners = lb[lb["is_winner"]]
        total_people = int(lb["name"].nunique())
        winner_count = int(winners["name"].nunique())

        st.markdown(
            f"""
<div class="kpiRow">
  <div class="kpi"><div class="label">Participants</div><div class="value">{total_people}</div></div>
  <div class="kpi"><div class="label">Winners</div><div class="value">{winner_count}</div></div>
  <div class="kpi"><div class="label">Cutoff</div><div class="value">{WINNER_CUTOFF}</div></div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.write("")
        show = lb.copy()
        show["status"] = np.where(show["is_winner"], "🏆 Winner", "")
        show["progress_%"] = (show["progress"] * 100).round(0).astype(int)

        st.dataframe(
            show[["status", "name", "qualifying_days", "workouts_left", "workout_days", "progress_%"]].rename(
                columns={
                    "name": "Name",
                    "qualifying_days": "Qualifying Days (>=250)",
                    "workouts_left": "Workouts Left",
                    "workout_days": "Workout Days (any)",
                    "progress_%": "Progress %",
                    "status": " ",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Workouts left (by person)")

        people = sorted(lb["name"].dropna().unique().tolist())
        who = st.selectbox("Filter by name", people)

        row = lb[lb["name"] == who].iloc[0]
        remaining = int(row["workouts_left"])
        qdays = int(row["qualifying_days"])
        wdays = int(row["workout_days"])

        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown(f"### {who}")
        st.markdown(f"- Qualifying: **{qdays} / {WINNER_CUTOFF}**")
        st.markdown(f"- Workout days (any): **{wdays}**")
        st.markdown(f"#### Remaining: **{remaining}**")
        if remaining == 0:
            st.success("Winner locked 🔥")
        else:
            st.info("Not there yet — keep going 💪")
        st.markdown("</div>", unsafe_allow_html=True)

        # tiny chart: qualifying by day-of-month (nice quick visual)
        style_plots()
        person = df_month[df_month["name"] == who].copy()
        q = person[person["burnt_250"]].copy()
        if not q.empty:
            q["dom"] = pd.to_datetime(q["workout_date"]).dt.day
            g = q.groupby("dom")["workout_date"].count().reset_index(name="count")

            fig, ax = plt.subplots(figsize=(6.1, 2.4))
            sns.barplot(data=g, x="dom", y="count", ax=ax)
            set_title_labels(ax, "Qualifying workouts by day-of-month", "Day", "Count")
            ax.tick_params(axis="x", labelrotation=0)
            st.pyplot(fig)
        else:
            st.caption("No qualifying workouts yet for this person.")
        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Scorecard
# =========================
elif tab == "Scorecard":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Scorecard")
    st.markdown("<div class='small-muted'>Longest streak • fastest winner • lazy logger • front-loading vs cramming • barely missed</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Longest streak (qualifying)
    streak_rows = []
    for name, g in df_month[df_month["burnt_250"]].groupby("name"):
        streak_rows.append({"name": name, "longest_streak": longest_streak(g["workout_date"].dropna().tolist())})
    streak_df = pd.DataFrame(streak_rows).sort_values("longest_streak", ascending=False)

    # Fastest winner
    fw_rows = []
    for name in df_month["name"].dropna().unique():
        fw = fastest_winner_date(df_month, name, WINNER_CUTOFF)
        if fw:
            fw_rows.append({"name": name, "hit_cutoff_on": fw})
    fw_df = pd.DataFrame(fw_rows).sort_values("hit_cutoff_on") if fw_rows else pd.DataFrame(columns=["name", "hit_cutoff_on"])

    # Lazy logger
    lazy_df = lazy_logger_score(df_month)

    # Front-load vs cram
    fl = frontload_vs_cram(df_month)

    # Barely missed + consistent-not-qualifying
    barely_missed = lb[(~lb["is_winner"]) & (lb["qualifying_days"].isin([WINNER_CUTOFF-2, WINNER_CUTOFF-1]))]
    consistent_not_qual = lb[(~lb["is_winner"]) & (lb["workout_days"] >= WINNER_CUTOFF)]

    a, b, c = st.columns(3, gap="large")

    with a:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### 🔥 Longest streak")
        if not streak_df.empty:
            st.markdown(f"**Leader:** {streak_df.iloc[0]['name']} — **{int(streak_df.iloc[0]['longest_streak'])} days**")
            st.dataframe(streak_df.head(10), hide_index=True, use_container_width=True)
        else:
            st.caption("No qualifying streaks yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with b:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### 🏁 Fastest winner")
        if not fw_df.empty:
            st.markdown(f"**Fastest:** {fw_df.iloc[0]['name']} — cutoff on **{fw_df.iloc[0]['hit_cutoff_on']}**")
            st.dataframe(fw_df.head(10), hide_index=True, use_container_width=True)
        else:
            st.caption("No winners yet (or not enough qualifying days).")
        st.markdown("</div>", unsafe_allow_html=True)

    with c:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### 🐢 Lazy logger")
        if lazy_df is not None and not lazy_df.empty:
            st.markdown(f"**Most delayed:** {lazy_df.iloc[0]['name']} — avg **{lazy_df.iloc[0]['avg_log_delay_days']:.2f} days**")
            st.dataframe(lazy_df.head(10), hide_index=True, use_container_width=True)
        else:
            st.caption("Need a timestamp column to compute this.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    left, right = st.columns([1.15, 1], gap="large")

    with left:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### 📦 Front-loading vs Cramming")
        if not fl.empty:
            st.dataframe(fl, hide_index=True, use_container_width=True)
            style_plots()
            fig, ax = plt.subplots(figsize=(7.2, 3.0))
            sns.countplot(data=fl, x="style", ax=ax)
            set_title_labels(ax, "Distribution of styles", "Style", "People")
            st.pyplot(fig)
        else:
            st.caption("Not enough data.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        st.markdown("### 😮 Barely missed & consistent-but-not-qualifying")
        st.caption("Barely missed = cutoff-2 or cutoff-1 qualifying days (not a winner).")
        st.dataframe(barely_missed[["name","qualifying_days","workouts_left","workout_days"]], hide_index=True, use_container_width=True)

        st.caption("Consistent but not qualifying = workout_days >= cutoff, qualifying_days < cutoff.")
        st.dataframe(consistent_not_qual[["name","qualifying_days","workouts_left","workout_days"]], hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Personalization
# =========================
elif tab == "Personalization":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Personalization: Day-of-week trends")
    st.markdown("<div class='small-muted'>Pick a person and compare their weekday pattern vs overall.</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    people = sorted(df_month["name"].dropna().unique().tolist())
    who = st.selectbox("Person", people)

    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    style_plots()
    overall = (
        df_month[df_month["any_workout"]]
        .groupby("dow")["workout_date"].nunique()
        .reindex(weekday_order)
        .reset_index(name="unique_days")
    )

    person = (
        df_month[(df_month["name"] == who) & (df_month["any_workout"])]
        .groupby("dow")["workout_date"].nunique()
        .reindex(weekday_order)
        .reset_index(name="unique_days")
    )

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6.8, 3.0))
        sns.barplot(data=overall, x="dow", y="unique_days", ax=ax)
        set_title_labels(ax, "Overall workouts by weekday", "Weekday", "Unique workout days")
        ax.tick_params(axis="x", labelrotation=20)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(6.8, 3.0))
        sns.barplot(data=person, x="dow", y="unique_days", ax=ax)
        set_title_labels(ax, f"{who}: workouts by weekday", "Weekday", "Unique workout days")
        ax.tick_params(axis="x", labelrotation=20)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Month-over-month
# =========================
else:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Month-over-month Trends")
    st.markdown("<div class='small-muted'>Participation, winners, and qualifying intensity over time.</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # participants per month
    participants = df[df["any_workout"]].groupby("month")["name"].nunique().reset_index(name="participants")

    # total unique workout days logged (across all people)
    total_workouts = df[df["any_workout"]].groupby("month")["workout_date"].nunique().reset_index(name="total_workout_days_logged")

    # avg qualifying days per person per month
    qual = (
        df[df["burnt_250"]]
        .groupby(["month","name"])["workout_date"].nunique()
        .reset_index(name="qualifying_days")
    )
    avg_qual = qual.groupby("month")["qualifying_days"].mean().reset_index(name="avg_qualifying_days_per_person")

    # winners per month
    winners = qual.copy()
    winners["is_winner"] = winners["qualifying_days"] >= WINNER_CUTOFF
    winner_count = winners[winners["is_winner"]].groupby("month")["name"].nunique().reset_index(name="winner_count")

    mom = (
        participants.merge(total_workouts, on="month", how="left")
        .merge(avg_qual, on="month", how="left")
        .merge(winner_count, on="month", how="left")
        .fillna({"winner_count": 0, "avg_qualifying_days_per_person": 0})
        .sort_values("month")
        .reset_index(drop=True)
    )

    st.dataframe(mom, hide_index=True, use_container_width=True)

    style_plots()
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7.2, 3.0))
        sns.lineplot(data=mom, x="month", y="participants", marker="o", ax=ax)
        set_title_labels(ax, "Participants per month", "Month", "Participants")
        ax.tick_params(axis="x", labelrotation=20)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7.2, 3.0))
        sns.lineplot(data=mom, x="month", y="winner_count", marker="o", ax=ax)
        set_title_labels(ax, "Winners per month", "Month", "Winners")
        ax.tick_params(axis="x", labelrotation=20)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='cardSolid'>", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7.2, 3.0))
        sns.lineplot(data=mom, x="month", y="avg_qualifying_days_per_person", marker="o", ax=ax)
        set_title_labels(ax, "Avg qualifying days per person", "Month", "Avg qualifying days")
        ax.tick_params(axis="x", labelrotation=20)
        st.pyplot(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
