"""Data source helpers: reading and cleaning raw sheet data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

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

# ---------------------------------------------------------------------------
# Whitespace-collapse regex used by `normalize_name`. Compiled once.
# ---------------------------------------------------------------------------
_WHITESPACE_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Authorized gspread client.
#
# `st.cache_data` caches function *outputs*; the gspread client itself is a
# resource (network connection + token state) and should be cached via
# `st.cache_resource` so we don't rebuild credentials on every cache miss
# of the data layer (adversarial P3-14).
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _get_gspread_client() -> gspread.Client:
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


@st.cache_data(ttl=60, show_spinner=False)
def read_google_sheet_as_df(spreadsheet_id: str, worksheet_name: str) -> pd.DataFrame:
    """Read a worksheet into a DataFrame using the cached gspread client.

    Empty cells are normalized to ``pd.NA`` and fully-empty rows are
    dropped. Schema validation is the caller's responsibility — this
    function only handles the I/O.
    """
    gc = _get_gspread_client()
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


# ---------------------------------------------------------------------------
# Name normalization.
#
# Single helper used by BOTH the form-responses loader and the roster loader
# so a name like " Ann   Smith " in one sheet can be joined to "Ann Smith"
# in the other. Without this, the leaderboard silently splits one person
# across two rows. (Adversarial review P1-04.)
# ---------------------------------------------------------------------------
def normalize_name(value: object) -> str:
    """Return a canonical form of a participant name.

    - Coerces ``NaN`` / ``None`` / ``pd.NA`` to ``""``.
    - Strips leading/trailing whitespace.
    - Collapses internal runs of whitespace to a single space.
    - Drops the literal placeholder strings pandas / Python emit when
      coercing missing values via ``str(x)`` (``"nan"``, ``"None"``,
      ``"<NA>"``).
    """
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = _WHITESPACE_RE.sub(" ", str(value)).strip()
    if text in {"nan", "None", "<NA>"}:
        return ""
    return text


def _month_label(month_str: str) -> str:
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
    except ValueError:
        return ""
    return dt.strftime("%B %Y")


# ---------------------------------------------------------------------------
# Typed `get_users` result.
#
# The previous implementation returned ``list[str] | None`` for *every*
# failure mode (read error, missing column, empty roster, no active users).
# Callers therefore could not distinguish "Sheets is down" from "no one is
# In this month" and silently fell back to "everyone with a workout row"
# — a documented adversarial finding (P0-04 / P1-07).
# ---------------------------------------------------------------------------
class GetUsersStatus(str, Enum):
    OK = "ok"
    READ_ERROR = "read_error"
    EMPTY_SHEET = "empty_sheet"
    MISSING_NAME_COLUMN = "missing_name_column"
    MISSING_MONTH_COLUMN = "missing_month_column"
    NO_ACTIVE_USERS = "no_active_users"


@dataclass(frozen=True)
class GetUsersResult:
    """Typed result for `get_users`.

    `users` is the resolved roster (possibly empty). `status` describes
    *why* the result looks the way it does so the caller can make a
    deliberate choice — fall back, warn, or fail loud — instead of
    treating every failure as "missing data".
    """

    users: list[str]
    status: GetUsersStatus
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status is GetUsersStatus.OK

    def __bool__(self) -> bool:
        return bool(self.users)

    def __iter__(self):
        return iter(self.users)

    def __len__(self) -> int:
        return len(self.users)


@st.cache_data(ttl=60, show_spinner=False)
def get_users(month_str: str | None = None) -> GetUsersResult:
    """Read the active-users roster.

    When ``month_str`` is provided, filter to participants whose status
    in that month's column matches ``USERS_STATUS_IN_VALUE``. Returns a
    `GetUsersResult` that distinguishes every failure mode so the caller
    cannot silently fall back to "everyone".
    """
    try:
        users_df = read_google_sheet_as_df(SPREADSHEET_ID, USERS_WORKSHEET_NAME)
    except Exception as exc:
        return GetUsersResult(
            users=[],
            status=GetUsersStatus.READ_ERROR,
            message=f"Could not read Users sheet: {type(exc).__name__}",
        )

    if users_df.empty:
        return GetUsersResult(users=[], status=GetUsersStatus.EMPTY_SHEET, message="Users sheet is empty.")

    if USERS_NAME_COLUMN not in users_df.columns:
        return GetUsersResult(
            users=[],
            status=GetUsersStatus.MISSING_NAME_COLUMN,
            message=f"Users sheet missing column: '{USERS_NAME_COLUMN}'.",
        )

    if month_str:
        month_label = _month_label(month_str)
        if not month_label or month_label not in users_df.columns:
            # Do NOT silently fall back to "everyone in the sheet" when the
            # month column is missing. Surface the degradation.
            return GetUsersResult(
                users=[],
                status=GetUsersStatus.MISSING_MONTH_COLUMN,
                message=(
                    f"Users sheet has no column for '{month_label or month_str}'. "
                    "Add the month column to the Venmo Tracker sheet to enable "
                    "the current-month roster filter."
                ),
            )
        in_value = USERS_STATUS_IN_VALUE.strip().lower()
        status = users_df[month_label].astype(str).str.strip().str.lower()
        users_df = users_df[status == in_value]

    names = users_df[USERS_NAME_COLUMN].apply(normalize_name)
    names = names[names != ""].drop_duplicates()
    users = names.tolist()
    if not users:
        return GetUsersResult(
            users=[],
            status=GetUsersStatus.NO_ACTIVE_USERS,
            message="No users found in Users sheet after filtering.",
        )
    return GetUsersResult(users=users, status=GetUsersStatus.OK)


def normalize_bool(x: object) -> bool:
    """Coerce a sheet cell to ``bool``.

    Treats common truthy spellings (``yes``, ``true``, ``1``, ``y``, ``t``)
    as ``True``; everything else (including ``NaN`` / ``None``) is ``False``.
    Used to normalize the form's ``Burnt >= 250 calories?`` checkbox before
    downstream metrics consume it.
    """
    if pd.isna(x):
        return False
    s = str(x).strip().lower()
    return s in {"yes", "true", "1", "y", "t"}


# ---------------------------------------------------------------------------
# Data-quality report attached to `clean()` output.
#
# `clean()` previously dropped malformed rows silently. The leaderboard
# could undercount a participant and the app would render confidently with
# the wrong number. The quality report is attached to the returned
# DataFrame via `df.attrs["quality_report"]` so:
#
#   - existing callers that just iterate the DataFrame are unaffected
#   - debug expanders / admin views can show the drop counts (P1-05)
# ---------------------------------------------------------------------------
@dataclass
class CleanQualityReport:
    rows_in: int = 0
    rows_out: int = 0
    dropped_blank_name: int = 0
    dropped_nat_timestamp: int = 0
    dropped_nat_workout_date: int = 0
    dropped_too_old: int = 0
    dropped_future: int = 0
    dropped_logged_in_future: int = 0
    dropped_bad_calories: int = 0
    dropped_calories_out_of_range: int = 0
    dropped_dedupe: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def total_dropped(self) -> int:
        """Count of rows dropped for *quality* reasons.

        Deliberately excludes ``dropped_dedupe`` — deduplicating
        ``(name, workout_date)`` and keeping the latest timestamp is
        normal app behaviour (people resubmit / correct entries) and
        does not indicate a data-quality problem. The dedupe count is
        still surfaced via :meth:`as_dict` for visibility when the
        expander does open for some other reason.
        """
        return (
            self.dropped_blank_name
            + self.dropped_nat_timestamp
            + self.dropped_nat_workout_date
            + self.dropped_too_old
            + self.dropped_future
            + self.dropped_logged_in_future
            + self.dropped_bad_calories
            + self.dropped_calories_out_of_range
        )

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d["total_dropped"] = self.total_dropped
        d["total_dropped_including_dedupe"] = self.total_dropped + self.dropped_dedupe
        return d


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
    3. **Timestamp parsing** — coerce to datetime; drop NaT timestamp rows.
    4. **Workout date parsing** — coerce to date; drop NaT workout_date rows.
    5. **Date sanity** — drop too-old / future / logged-in-future rows.
    6. **Calorie sanity** — drop garbage / out-of-range; keep blanks as NaN.
    7. **Boolean reconciliation** — when calories present, derive
       ``burnt_250`` from ``calories_burned >= 250`` and set
       ``calories_met_250`` to a tri-state nullable boolean (``pd.NA``
       when calories are blank — adversarial P1-02).
    8. **Dedupe** — keep latest timestamp per ``(name, workout_date)``.
    9. **Derived columns** — month / dow (str) / dow_num (int) / dom /
       log_delay_days (clamped >= 0) / any_workout.

    A `CleanQualityReport` is attached via ``df.attrs["quality_report"]``
    so admin / debug expanders can surface drop counts without changing
    the call signature.
    """
    df = df.copy()
    report = CleanQualityReport(rows_in=len(df))

    # --- Stage 1: schema check -------------------------------------------------
    expected = {col_timestamp, col_name, col_wkdate, col_250}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found columns: {list(df.columns)}")

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
    df["name"] = df["name_raw"].apply(normalize_name)
    blank_name = df["name"] == ""
    if blank_name.any():
        report.dropped_blank_name = int(blank_name.sum())
        df = df[~blank_name].reset_index(drop=True)

    # --- Stage 3: timestamp parsing -------------------------------------------
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    nat_ts = df["timestamp"].isna()
    if nat_ts.any():
        report.dropped_nat_timestamp = int(nat_ts.sum())
        df = df[~nat_ts].reset_index(drop=True)
    df["timestamp_date"] = df["timestamp"].dt.date

    # --- Stage 4: workout date parsing ----------------------------------------
    df["workout_date"] = pd.to_datetime(df["workout_date_raw"], errors="coerce").dt.date
    nat_wd = df["workout_date"].isna()
    if nat_wd.any():
        report.dropped_nat_workout_date = int(nat_wd.sum())
        df = df[~nat_wd].reset_index(drop=True)

    df["burnt_250"] = df["burnt_250_raw"].apply(normalize_bool)

    # --- Stage 5: date sanity -------------------------------------------------
    today = today_app()

    too_old = df["workout_date"].apply(lambda d: d < MIN_WORKOUT_DATE)
    if too_old.any():
        report.dropped_too_old = int(too_old.sum())
        df = df[~too_old].reset_index(drop=True)

    future_workout = df["workout_date"].apply(lambda d: d > today)
    if future_workout.any():
        report.dropped_future = int(future_workout.sum())
        df = df[~future_workout].reset_index(drop=True)

    grace = timedelta(days=1)
    if not df.empty:
        logged_in_future = df.apply(lambda r: r["workout_date"] > (r["timestamp_date"] + grace), axis=1)
        if logged_in_future.any():
            report.dropped_logged_in_future = int(logged_in_future.sum())
            df = df[~logged_in_future].reset_index(drop=True)

    # --- Stage 6: calorie sanity ----------------------------------------------
    if has_calories:
        df["calories_burned"] = pd.to_numeric(df["calories_raw"], errors="coerce")
        raw_filled = df["calories_raw"].notna() & (df["calories_raw"].astype(str).str.strip() != "")
        bad_input = raw_filled & df["calories_burned"].isna()
        if bad_input.any():
            report.dropped_bad_calories = int(bad_input.sum())
            df = df[~bad_input].reset_index(drop=True)

        in_range = df["calories_burned"].isna() | (
            (df["calories_burned"] >= 0) & (df["calories_burned"] <= MAX_CALORIES)
        )
        out_of_range_count = int((~in_range).sum())
        if out_of_range_count:
            report.dropped_calories_out_of_range = out_of_range_count
            df = df[in_range].reset_index(drop=True)

        # --- Stage 7: bool/calorie reconciliation -----------------------------
        has_num = df["calories_burned"].notna()
        df.loc[has_num, "burnt_250"] = df.loc[has_num, "calories_burned"] >= 250

        # Use a nullable boolean dtype so blank-calorie rows surface as
        # `pd.NA` (= "calories not provided"), distinct from `False`
        # (= "provided and below 250"). Adversarial finding P1-02.
        met = pd.array([pd.NA] * len(df), dtype="boolean")
        if has_num.any():
            mask_values = has_num.to_numpy()
            met[mask_values] = (df.loc[has_num, "calories_burned"] >= 250).astype(bool).to_numpy()
        df["calories_met_250"] = met
    else:
        df["calories_burned"] = pd.NA
        df["calories_met_250"] = pd.array([pd.NA] * len(df), dtype="boolean")

    # --- Stage 8: dedupe ------------------------------------------------------
    if dedupe:
        before = len(df)
        df = (
            df.sort_values("timestamp", ascending=True)
            .drop_duplicates(subset=["name", "workout_date"], keep="last")
            .reset_index(drop=True)
        )
        report.dropped_dedupe = before - len(df)

    # --- Stage 9: derived columns --------------------------------------------
    df["any_workout"] = df["workout_date"].notna()
    df["workout_dt"] = pd.to_datetime(df["workout_date"], errors="coerce")
    month_period = df["workout_dt"].dt.to_period("M")
    df["month"] = month_period.astype(str).where(month_period.notna(), pd.NA)
    # `dow` retained as the day-name string (used by every existing UI as
    # a display label and groupby key). `dow_num` added for callers that
    # need a deterministic integer (Mon=0..Sun=6). The `agents.md` domain
    # model has been updated to match this dual representation.
    df["dow"] = df["workout_dt"].dt.day_name()
    df["dow_num"] = df["workout_dt"].dt.dayofweek.astype("Int64")
    df["dom"] = df["workout_dt"].dt.day

    raw_delay = (
        pd.to_datetime(df["timestamp_date"], errors="coerce") - pd.to_datetime(df["workout_date"], errors="coerce")
    ).dt.days
    # Clamp negative delays (timezone-grace artifacts) to 0 — "logged the
    # same day" — instead of leaving e.g. -1 to skew Lazy Logger averages.
    # Adversarial finding P1-06.
    df["log_delay_days"] = raw_delay.clip(lower=0)

    report.rows_out = len(df)
    df.attrs["quality_report"] = report
    return df


@st.cache_data(ttl=60, show_spinner=False)
def get_data() -> pd.DataFrame:
    """Read + clean the Form Responses sheet.

    Surfaces user-friendly errors at the UI boundary. The full exception
    is shown in a debug expander rather than via `st.exception` so we
    don't leak stack traces into the main view (adversarial P3-12).
    """
    try:
        raw = read_google_sheet_as_df(SPREADSHEET_ID, WORKSHEET_NAME)
    except Exception as exc:
        st.error("Could not read the workouts sheet. Check that the service account has access to the Google Sheet.")
        with st.expander("Show debug details", expanded=False):
            st.exception(exc)
        st.stop()

    try:
        df = clean(raw, dedupe=True)
    except Exception as exc:
        st.error("Data cleaning failed. The most likely cause is a header mismatch in the form.")
        with st.expander("Show debug details", expanded=False):
            st.exception(exc)
        st.stop()

    return df
