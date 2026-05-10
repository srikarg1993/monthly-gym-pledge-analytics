# =========================================================
# Google Sheets configuration
# =========================================================
from datetime import date as _date

SPREADSHEET_ID = "17RADj_LH-Lj_lB8QFZyxjv8iKFerNZfNT-7wmtPNuzk"
WORKSHEET_NAME = "Form Responses"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# =========================================================
# Users / roster sheet
# =========================================================
USERS_WORKSHEET_NAME = "Venmo Tracker"
USERS_NAME_COLUMN = "Participant"
USERS_STATUS_IN_VALUE = "In"

# =========================================================
# Pledge rules (single source of truth)
#
# These are the visible business rules. ``WINNER_CUTOFF`` is the default
# qualifying-day target; per-month exceptions live in
# ``WINNER_CUTOFF_BY_MONTH`` and resolve through ``winner_cutoff_for_month``.
# Every UI module that needs to display the rule MUST import from here
# rather than hard-coding a literal — that drift is what the 2026-05-10
# adversarial review caught (About said 16 while February resolved to 15).
# =========================================================
PLEDGE_AMOUNT_USD = 10
WINNER_CUTOFF = 16
QUALIFYING_DAYS = WINNER_CUTOFF  # display alias for UI copy
DAILY_CALORIE_TARGET = 250
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

# =========================================================
# External links (operational, not secret).
#
# Moved out of UI modules so the same value can't drift between About,
# Log Your Workout, and any future page that wants to reference it.
# =========================================================
VENMO_HANDLE = "@maddaladivya3212"
VENMO_LINK = "https://venmo.com/u/maddaladivya3212"

WORKOUT_FORM_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSeaWgRsPcMfZjwzZ-6pH6qRr4Ev_BgKchxIDPEmHAbGVdbe8Q/viewform?usp=dialog"
)
WORKOUT_FORM_EMBED_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSeaWgRsPcMfZjwzZ-6pH6qRr4Ev_BgKchxIDPEmHAbGVdbe8Q/viewform?embedded=true"
)

# =========================================================
# Privacy posture (documented, not enforced).
#
# This dashboard runs publicly on Streamlit Community Cloud. There is no
# auth gate today; access is "URL only" + private-group obscurity.
# Treated as acceptable for a friend-group app, but documented here so
# the next contributor cannot accidentally believe an auth layer exists.
# See [`docs/adr/0010-privacy-posture.md`](../../docs/adr/0010-privacy-posture.md).
# =========================================================
PRIVACY_MODEL = "url-obscurity"


def winner_cutoff_for_month(month_str) -> int:
    """Resolve the winner cutoff (qualifying-days target) for a month.

    ``month_str`` is a ``YYYY-MM`` string. Falls back to ``WINNER_CUTOFF``
    when the month is not in the per-month overrides table. Coerces
    non-int overrides defensively so a typo in ``WINNER_CUTOFF_BY_MONTH``
    cannot crash the leaderboard.
    """
    cutoff = WINNER_CUTOFF_BY_MONTH.get(str(month_str), WINNER_CUTOFF)
    try:
        return max(int(cutoff), 1)
    except (TypeError, ValueError):
        return WINNER_CUTOFF
