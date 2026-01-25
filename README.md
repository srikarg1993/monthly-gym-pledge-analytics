# Monthly Gym Pledge Analytics

Streamlit dashboard for a monthly fitness pledge, backed by a Google Form and Google Sheet.

## Features
- Sidebar navigation: About us, Leaderboard, Scorecard, Log Your Workout
- Leaderboard for the current month
- Scorecard and month-specific views
- Workout logging CTA that opens the Google Form

## Setup
1) Install dependencies:

```bash
pip install -r requirements.txt
```

2) Configure Google Sheets access:
- Create a service account in GCP and download the JSON.
- In Streamlit, store it as secrets under `gcp_service_account`.
- Share the Google Sheet with the service-account email.

Example `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

3) Update app settings in `gym_pledge/config/globals.py`:
- `SPREADSHEET_ID`
- `WORKSHEET_NAME`
- `WINNER_CUTOFF`
- `USERS_WORKSHEET_NAME`
- `USERS_NAME_COLUMN`
- `USERS_STATUS_IN_VALUE`

## Run

```bash
streamlit run gym_pledge/dashboard.py
```

## Project layout
- `gym_pledge/dashboard.py`: app shell and sidebar navigation
- `gym_pledge/ui/`: UI pages (leaderboard, scorecard, log your workout, about)
- `gym_pledge/data/`: data loading and cleanup
- `gym_pledge/data/metrics.py`: data metrics and leaderboard logic
- `gym_pledge/styles/theme.css`: app styling
