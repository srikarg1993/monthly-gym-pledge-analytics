import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from config.globals import *


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

def get_data() -> pd.DataFrame:
    try:
        raw = read_google_sheet_as_df(SPREADSHEET_ID, WORKSHEET_NAME)
    except Exception as e:
        st.error("Could not read Google Sheet. Check: secrets/service_account.json and share the sheet with the service-account email.")
        st.exception(e)
        st.stop()

    try:
        df = clean(raw, dedupe=True)
    except Exception as e:
        st.error("Data cleaning failed (header mismatch is most likely).")
        st.exception(e)
        st.stop()
    
    return df
    