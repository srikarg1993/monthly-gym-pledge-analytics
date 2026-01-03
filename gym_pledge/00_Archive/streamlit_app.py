
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Gym Kitty Dashboard", layout="wide")

st.title("Gym Kitty Dashboard")

st.markdown("""
This dashboard reads the same dataset as the notebook and provides:

- Monthly winners and leaderboards
- Day-of-week patterns
- Logging delay analysis
- Front-loading vs cramming
- Streaks and "barely missed"
- Month-over-month trends and awards
""")

# --------------------
# Helpers (same logic as notebook, lightly simplified)
# --------------------
def normalize_bool(x):
    if pd.isna(x):
        return False
    s = str(x).strip().lower()
    return s in {"yes", "true", "1", "y", "t"}

def clean(df: pd.DataFrame, col_timestamp, col_name, col_wkdate, col_250) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns={
        col_timestamp: "timestamp",
        col_name: "name",
        col_wkdate: "workout_date",
        col_250: "burnt_250_raw",
    })

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["workout_date"] = pd.to_datetime(df["workout_date"], errors="coerce").dt.date

    df["name"] = (
        df["name"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    df["burnt_250"] = df["burnt_250_raw"].apply(normalize_bool)
    df["any_workout"] = df["workout_date"].notna()

    df = df.sort_values(["name", "workout_date", "timestamp"])
    df = df.drop_duplicates(subset=["name", "workout_date"], keep="first")

    df["workout_dt"] = pd.to_datetime(df["workout_date"])
    df["month"] = df["workout_dt"].dt.to_period("M").astype(str)
    df["dow"] = df["workout_dt"].dt.day_name()
    df["timestamp_date"] = df["timestamp"].dt.date
    df["log_delay_days"] = (pd.to_datetime(df["timestamp_date"]) - pd.to_datetime(df["workout_date"])).dt.days
    df["dom"] = df["workout_dt"].dt.day
    return df

def monthly_summary(df: pd.DataFrame, cutoff: int) -> pd.DataFrame:
    qualifying = (
        df[df["burnt_250"] & df["any_workout"]]
        .groupby(["month", "name"])["workout_date"]
        .nunique()
        .reset_index(name="qualifying_days_250")
    )
    any_days = (
        df[df["any_workout"]]
        .groupby(["month", "name"])["workout_date"]
        .nunique()
        .reset_index(name="workout_days_any")
    )
    out = any_days.merge(qualifying, on=["month", "name"], how="left")
    out["qualifying_days_250"] = out["qualifying_days_250"].fillna(0).astype(int)
    out["is_winner"] = out["qualifying_days_250"] >= cutoff
    return out

def longest_streak(dates: list) -> int:
    if not dates:
        return 0
    ds = sorted(set(pd.to_datetime(dates).date))
    best = cur = 1
    for i in range(1, len(ds)):
        if (pd.to_datetime(ds[i]) - pd.to_datetime(ds[i-1])).days == 1:
            cur += 1
            best = max(best, cur)
        else:
            cur = 1
    return best

def streaks(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["any_workout"]].copy()
    rows = []
    for (m, name), g in d.groupby(["month", "name"]):
        any_dates = g["workout_date"].dropna().tolist()
        q_dates = g.loc[g["burnt_250"], "workout_date"].dropna().tolist()
        rows.append({
            "month": m,
            "name": name,
            "longest_streak_any": longest_streak(any_dates),
            "longest_streak_250": longest_streak(q_dates),
        })
    return pd.DataFrame(rows)

def delay_summary(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["any_workout"]].copy()
    return (
        d.groupby(["month","name"])["log_delay_days"]
        .agg(submissions="count", mean_delay="mean", median_delay="median", same_day_rate=lambda x: float(np.mean(x == 0)))
        .reset_index()
    )

def frontload_cram(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["any_workout"]].copy()
    d["month_period"] = pd.to_datetime(d["month"] + "-01").dt.to_period("M")
    d["days_in_month"] = d["month_period"].dt.days_in_month

    rows = []
    for (m, name), g in d.groupby(["month","name"]):
        dom = g["dom"].to_numpy()
        dim = int(g["days_in_month"].iloc[0])
        share_first10 = float(np.mean(dom <= 10)) if len(dom) else np.nan
        share_last10 = float(np.mean(dom >= (dim - 9))) if len(dom) else np.nan
        rows.append({
            "month": m,
            "name": name,
            "avg_day_of_month": float(np.mean(dom)) if len(dom) else np.nan,
            "share_first_10_days": share_first10,
            "share_last_10_days": share_last10,
            "cram_score": (share_last10 or 0) - (share_first10 or 0),
        })
    return pd.DataFrame(rows)

# --------------------
# Inputs
# --------------------
st.sidebar.header("Data source")

data_mode = st.sidebar.radio("Choose input", ["Upload CSV", "Google Sheet CSV URL"])

default_cols = {
    "Timestamp": "Timestamp",
    "Name": "You are?",
    "Workout date": "Workout date",
    ">=250?": "Burnt >= 250 calories?",
}

if data_mode == "Upload CSV":
    up = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if not up:
        st.info("Upload a CSV to begin.")
        st.stop()
    raw = pd.read_csv(up)
else:
    url = st.sidebar.text_input("Google Sheet CSV URL", value="")
    if not url:
        st.info("Paste a Google Sheet CSV export URL to begin.")
        st.stop()
    raw = pd.read_csv(url)

st.sidebar.header("Column mapping")
col_timestamp = st.sidebar.text_input("Timestamp column", value=default_cols["Timestamp"])
col_name      = st.sidebar.text_input("Name column", value=default_cols["Name"])
col_wkdate    = st.sidebar.text_input("Workout date column", value=default_cols["Workout date"])
col_250       = st.sidebar.text_input(">=250 column", value=default_cols[">=250?"])

cutoff = st.sidebar.number_input("Winner cutoff (qualifying days)", min_value=1, max_value=31, value=16)

df = clean(raw, col_timestamp, col_name, col_wkdate, col_250)
ms = monthly_summary(df, cutoff=cutoff)
si = streaks(df)
ld = delay_summary(df)
fc = frontload_cram(df)

months = sorted(ms["month"].unique().tolist())
if not months:
    st.warning("No valid workout_date values found.")
    st.stop()

selected_month = st.sidebar.selectbox("Month", months, index=len(months)-1)

# --------------------
# Main views
# --------------------
left, right = st.columns([1.3, 1])

with left:
    st.subheader("Winners and leaderboard")
    g = ms[ms["month"] == selected_month].sort_values(["is_winner","qualifying_days_250","workout_days_any"], ascending=[False, False, False])
    st.dataframe(g, use_container_width=True)

    st.subheader("Qualifying days leaderboard")
    top = g.sort_values("qualifying_days_250", ascending=False).head(20)
    fig = plt.figure()
    plt.bar(top["name"], top["qualifying_days_250"])
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Qualifying days (>=250)")
    plt.title(f"{selected_month}")
    plt.tight_layout()
    st.pyplot(fig)

with right:
    st.subheader("Barely missed (cutoff-2 to cutoff-1)")
    bm = g[(g["qualifying_days_250"] >= cutoff-2) & (g["qualifying_days_250"] <= cutoff-1)].sort_values("qualifying_days_250", ascending=False)
    st.dataframe(bm, use_container_width=True)

    st.subheader("Streaks")
    s = si[si["month"] == selected_month].sort_values("longest_streak_any", ascending=False)
    st.dataframe(s, use_container_width=True)

st.divider()

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("Day-of-week distribution")
    d = df[df["month"] == selected_month]
    overall = (
        d[d["any_workout"]]
        .groupby("dow")["workout_date"]
        .nunique()
        .reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
        .fillna(0)
        .astype(int)
    )
    fig = plt.figure()
    plt.bar(overall.index, overall.values)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Unique workout days logged")
    plt.title(f"{selected_month}")
    plt.tight_layout()
    st.pyplot(fig)

with c2:
    st.subheader("Logging delay (median days)")
    d2 = ld[ld["month"] == selected_month].sort_values("median_delay", ascending=False)
    st.dataframe(d2, use_container_width=True)

with c3:
    st.subheader("Front-load vs cramming")
    d3 = fc[fc["month"] == selected_month].sort_values("cram_score", ascending=False)
    st.dataframe(d3, use_container_width=True)

st.divider()

st.subheader("Month-over-month summary")
mom = (
    ms.groupby("month")
      .agg(
          participants=("name","nunique"),
          avg_qualifying=("qualifying_days_250","mean"),
          winner_count=("is_winner","sum"),
          avg_any=("workout_days_any","mean"),
      )
      .reset_index()
      .sort_values("month")
)
st.dataframe(mom, use_container_width=True)
