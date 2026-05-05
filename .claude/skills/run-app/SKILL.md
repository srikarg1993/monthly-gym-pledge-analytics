---
name: run-app
description: Start the Streamlit dashboard locally. Use when the user asks to "run the app", "start streamlit", "launch the dashboard", or wants to preview UI changes in the browser.
---

# Run the Streamlit app

The app is `gym_pledge/dashboard.py` and serves on port 8501.

## Preferred launcher

```bash
./start-app.sh
```

This kills any process currently bound to 8501 before starting, so it is safe to re-run.

## Direct invocation

```bash
streamlit run gym_pledge/dashboard.py
```

Use this when the venv-based `start-app.sh` isn't applicable (e.g., in the dev container, which already manages the port).

## Prerequisites

1. `pip install -r requirements.txt` (Python 3.11).
2. `gym_pledge/.streamlit/secrets.toml` must contain a GCP service-account JSON under `[gcp_service_account]`. The service account needs **Viewer** access to the spreadsheet referenced in `gym_pledge/config/globals.py` (`SPREADSHEET_ID`).
3. Optional: `export APP_TIMEZONE=America/Chicago` (default already `America/Chicago`). Override when testing month-boundary behavior.

## Verifying

- Open http://localhost:8501
- Sidebar should show: **Leaderboard**, **Scorecard**, **Year Calendar**, **Log your workout**, **About**. (`monthovermonth` and `personalization` pages exist but are intentionally hidden from the sidebar.)
- If data doesn't load, fall back to the `debug-sheets` skill.

## Common failure modes

- **Port already in use** → `start-app.sh` handles this; if using `streamlit run` directly, kill the process on 8501 first.
- **`KeyError: 'gcp_service_account'`** → secrets.toml is missing or malformed.
- **`SpreadsheetNotFound` / permission errors** → service-account email hasn't been shared on the sheet.
