"""Data source helpers: reading and cleaning raw sheet data."""

from datetime import datetime
from typing import List, Optional

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from config.globals import (
    SCOPES,
    SPREADSHEET_ID,
    WORKSHEET_NAME,
    USERS_WORKSHEET_NAME,
    USERS_NAME_COLUMN,
    USERS_STATUS_IN_VALUE,
    MAX_CALORIES,
)


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


def _month_label(month_str: str) -> str:
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        return ""
    return dt.strftime("%B %Y")


def get_users(month_str: Optional[str] = None) -> Optional[List[str]]:
    try:
        users_df = read_google_sheet_as_df(SPREADSHEET_ID, USERS_WORKSHEET_NAME)
    except Exception as e:
        st.warning("Could not read Users sheet. Check the sheet name and sharing permissions.")
        st.exception(e)
        return None

    if users_df.empty:
        st.warning("Users sheet is empty.")
        return None

    if USERS_NAME_COLUMN not in users_df.columns:
        st.warning(f"Users sheet missing column: '{USERS_NAME_COLUMN}'.")
        return None

    if month_str:
        month_label = _month_label(month_str)
        if month_label and month_label in users_df.columns:
            in_value = USERS_STATUS_IN_VALUE.strip().lower()
            status = users_df[month_label].astype(str).str.strip().str.lower()
            users_df = users_df[status == in_value]

    names = users_df[USERS_NAME_COLUMN].astype(str).str.strip()
    names = names.replace("", pd.NA).dropna().drop_duplicates()

    users = names.tolist()
    if not users:
        st.warning("No users found in Users sheet after filtering.")
        return None
    return users


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
    col_calories: str = "How many calories did you burn?",
    dedupe: bool = True,
) -> pd.DataFrame:
    df = df.copy()

    expected = {col_timestamp, col_name, col_wkdate, col_250}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns: {missing}. Found columns: {list(df.columns)}"
        )

    rename_map = {
        col_timestamp: "timestamp",
        col_name: "name_raw",
        col_wkdate: "workout_date_raw",
        col_250: "burnt_250_raw",
    }

    has_calories = col_calories in df.columns
    if has_calories:
        rename_map[col_calories] = "calories_raw"

    df = df.rename(columns=rename_map)

    df["name"] = (
        df["name_raw"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["timestamp_date"] = df["timestamp"].dt.date

    df["workout_date"] = pd.to_datetime(df["workout_date_raw"], errors="coerce").dt.date
    df["burnt_250"] = df["burnt_250_raw"].apply(normalize_bool)

    if has_calories:
        df["calories_burned"] = pd.to_numeric(df["calories_raw"], errors="coerce")
        # Only discard rows that had a non-empty, non-blank value which
        # turned out non-numeric (genuine garbage like "abc").
        raw_filled = df["calories_raw"].notna() & (df["calories_raw"].astype(str).str.strip() != "")
        bad_input = raw_filled & df["calories_burned"].isna()
        df = df[~bad_input].reset_index(drop=True)
        df = df[df["calories_burned"].isna() | (df["calories_burned"] <= MAX_CALORIES)].reset_index(drop=True)
        df["calories_met_250"] = df["calories_burned"] >= 250
    else:
        df["calories_burned"] = pd.NA
        df["calories_met_250"] = pd.NA

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
    
