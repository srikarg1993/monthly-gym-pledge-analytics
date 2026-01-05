USERS = {
    "Naveen Ganta",
    "Eshwar",
    "Srikar Gunisetty",
    "Sandesh Ghanta",
    "Surya Chaitanya",
    "Vennela Chava",
    "Pradyumna Ch.",
    "Srivatsav Gunisetty",
    "Divya Maddala",
    "Gayathri Ravipati",
    "Jahnavi"
}

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


WINNER_CUTOFF = 16