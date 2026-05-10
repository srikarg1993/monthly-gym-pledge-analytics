"""Data source helpers: reading and cleaning raw sheet data."""

from datetime import datetime

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from app_time import today_app
from config.globals import (
    MAX_CALORIES,
    MIN_WORKOUT_DATE,
    SCOPES,
    SPREADSHEET_ID,
    USERS_NAME_COLUMN,
    USERS_STATUS_IN_VALUE,
    USERS_WORKSHEET_NAME,
    WORKSHEET_NAME,
)


@st.cache_data(ttl=60, show_spinner=False)
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


@st.cache_data(ttl=60, show_spinner=False)
def get_users(month_str: str | None = None) -> list[str] | None:
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


def normalize_bool(x: object) -> bool:
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
    """Clean raw form responses into a canonical workout DataFrame.

    Filters applied, in order:

    1. **Schema check** — required columns must be present (raises otherwise).
    2. **Name normalization** — strip + collapse whitespace; drop blank names.
    3. **Timestamp parsing** — coerce to datetime; drop rows with NaT timestamp
       (we can't compute log delay without one).
    4. **Workout date parsing** — coerce to date; drop rows with NaT
       workout_date (every downstream metric bins by date).
    5. **Date sanity** — drop workout_date older than ``MIN_WORKOUT_DATE``
       (1999-03 typos), drop workout_date in the future relative to ``today``,
       and drop rows where workout_date is *after* the timestamp date
       (logging a workout for a date you haven't reached yet).
    6. **Calorie sanity** — drop genuine non-numeric garbage like "abc",
       drop negative values, and drop values above ``MAX_CALORIES``. Blank
       calories are kept as NaN.
    7. **Boolean reconciliation** — when a numeric calorie value is present,
       derive ``burnt_250`` from ``calories_burned >= 250`` (overriding the
       form checkbox so the bool and the number can never disagree).
    8. **Dedupe** — keep the latest timestamp per ``(name, workout_date)``.
    9. **Derived columns** — month/dow/dom/log_delay_days/any_workout.
    """
    df = df.copy()

    # --- Stage 1: schema check -------------------------------------------------
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

    # --- Stage 2: name normalization ------------------------------------------
    df["name"] = (
        df["name_raw"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    )
    # An empty/whitespace-only name represents a malformed submission. The
    # ``.astype(str)`` above turns NaN into the literal string "nan", so guard
    # against that too.
    blank_name = df["name"].isin({"", "nan", "None", "<NA>"})
    if blank_name.any():
        df = df[~blank_name].reset_index(drop=True)

    # --- Stage 3: timestamp parsing -------------------------------------------
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # No timestamp -> we can't tell when the row was logged, which breaks
    # log-delay metrics and dedupe ordering.
    df = df[df["timestamp"].notna()].reset_index(drop=True)
    df["timestamp_date"] = df["timestamp"].dt.date

    # --- Stage 4: workout date parsing ----------------------------------------
    df["workout_date"] = pd.to_datetime(df["workout_date_raw"], errors="coerce").dt.date
    # Every downstream metric (leaderboard, frontload/cram, year calendar,
    # weekday cadence) buckets rows by ``workout_date``. A NaT here means the
    # whole row is unusable.
    df = df[df["workout_date"].notna()].reset_index(drop=True)

    df["burnt_250"] = df["burnt_250_raw"].apply(normalize_bool)

    # --- Stage 5: date sanity -------------------------------------------------
    today = today_app()

    # 5a. Implausibly old: e.g. "1999-03-15" picked by accident in the form.
    too_old = df["workout_date"].apply(lambda d: d < MIN_WORKOUT_DATE)
    if too_old.any():
        df = df[~too_old].reset_index(drop=True)

    # 5b. Future-dated: typos when backfilling the date picker.
    future_workout = df["workout_date"].apply(lambda d: d > today)
    if future_workout.any():
        df = df[~future_workout].reset_index(drop=True)

    # 5c. Logged a workout for a date *after* the form was submitted. Even
    # when both dates are in the past, this is logically impossible — you
    # cannot have done a workout on a day you hadn't reached when you wrote
    # the form. Almost always a date-picker typo.
    logged_in_future = df.apply(
        lambda r: r["workout_date"] > r["timestamp_date"], axis=1
    )
    if logged_in_future.any():
        df = df[~logged_in_future].reset_index(drop=True)

    # --- Stage 6: calorie sanity ----------------------------------------------
    if has_calories:
        df["calories_burned"] = pd.to_numeric(df["calories_raw"], errors="coerce")
        # 6a. Genuine garbage like "abc": raw column was non-empty but failed
        # numeric coercion. Blanks are kept (-> NaN calories).
        raw_filled = df["calories_raw"].notna() & (
            df["calories_raw"].astype(str).str.strip() != ""
        )
        bad_input = raw_filled & df["calories_burned"].isna()
        if bad_input.any():
            df = df[~bad_input].reset_index(drop=True)

        # 6b. Out-of-range numerics (negative or above sane ceiling).
        in_range = df["calories_burned"].isna() | (
            (df["calories_burned"] >= 0) & (df["calories_burned"] <= MAX_CALORIES)
        )
        df = df[in_range].reset_index(drop=True)

        # --- Stage 7: bool/calorie reconciliation -----------------------------
        # When a numeric calorie value is present, it is the ground truth and
        # we override the self-reported checkbox. (Otherwise we trust the
        # form bool.)
        has_num = df["calories_burned"].notna()
        df.loc[has_num, "burnt_250"] = df.loc[has_num, "calories_burned"] >= 250

        df["calories_met_250"] = df["calories_burned"] >= 250
    else:
        df["calories_burned"] = pd.NA
        df["calories_met_250"] = pd.NA

    # --- Stage 8: dedupe ------------------------------------------------------
    if dedupe:
        df = (
            df.sort_values("timestamp", ascending=True)
            .drop_duplicates(subset=["name", "workout_date"], keep="last")
            .reset_index(drop=True)
        )

    # --- Stage 9: derived columns --------------------------------------------
    df["any_workout"] = df["workout_date"].notna()
    df["workout_dt"] = pd.to_datetime(df["workout_date"], errors="coerce")
    month_period = df["workout_dt"].dt.to_period("M")
    df["month"] = month_period.astype(str).where(month_period.notna(), pd.NA)
    df["dow"] = df["workout_dt"].dt.day_name()
    df["dom"] = df["workout_dt"].dt.day

    df["log_delay_days"] = (
        pd.to_datetime(df["timestamp_date"], errors="coerce")
        - pd.to_datetime(df["workout_date"], errors="coerce")
    ).dt.days

    return df


@st.cache_data(ttl=60, show_spinner=False)
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

