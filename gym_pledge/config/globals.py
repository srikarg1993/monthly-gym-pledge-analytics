# =========================================================
# Google Sheets auth (from notebook)
# =========================================================
from datetime import date as _date

SPREADSHEET_ID = "17RADj_LH-Lj_lB8QFZyxjv8iKFerNZfNT-7wmtPNuzk"
WORKSHEET_NAME = "Form Responses"
SERVICE_ACCOUNT_JSON_PATH = "secrets/service_account.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# =========================================================
# Users sheet (names)
# =========================================================
USERS_WORKSHEET_NAME = "Venmo Tracker"
USERS_NAME_COLUMN = "Participant"
USERS_STATUS_IN_VALUE = "In"


WINNER_CUTOFF = 16
MAX_CALORIES = 2200

# Workout dates older than this are treated as data-entry typos (e.g. someone
# accidentally picked "1999-03-15" in the date picker). The pledge began in
# January 2024, so any workout claimed before that is implausible.
MIN_WORKOUT_DATE = _date(2024, 1, 1)

# Optional per-month cutoff overrides (YYYY-MM).
# Keep WINNER_CUTOFF as the default for months not listed here.
WINNER_CUTOFF_BY_MONTH = {
    "2026-02": 15,
}


def winner_cutoff_for_month(month_str) -> int:
    """Resolve winner cutoff for a month string like YYYY-MM."""
    cutoff = WINNER_CUTOFF_BY_MONTH.get(str(month_str), WINNER_CUTOFF)
    try:
        return max(int(cutoff), 1)
    except (TypeError, ValueError):
        return WINNER_CUTOFF
