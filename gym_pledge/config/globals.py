# =========================================================
# Google Sheets auth (from notebook)
# =========================================================
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


WINNER_CUTOFF = 15
