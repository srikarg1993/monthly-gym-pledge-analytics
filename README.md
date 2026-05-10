# Monthly Gym Pledge Analytics

[![ci](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/ci.yml)
[![codeql](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/srikarg1993/monthly-gym-pledge-analytics/branch/main/graph/badge.svg)](https://codecov.io/gh/srikarg1993/monthly-gym-pledge-analytics)
[![python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Streamlit dashboard for a monthly fitness pledge, backed by a Google Form and Google Sheet.

> AI agents working on this repo: read [`agents.md`](agents.md) first. It captures the project's hard rules, layering, visual design language, and skill index.

## Features
- Sidebar navigation: About us, Leaderboard, Scorecard, Log Your Workout
- Leaderboard for the current month with active-user backfill
- Scorecard with modernized charts: qualifying progress ladder, cumulative calorie race, weekday cadence radar, longest streak heartbeat, Brick by Brick vs All-Nighter split, Lazy Logger bubble clusters
- Year calendar heatmap and month-over-month trends
- Workout logging CTA that opens the Google Form

## Documentation

- [`agents.md`](agents.md) — system prompt for any AI agent
- [`docs/adr/`](docs/adr/) — Architectural Decision Records
- [`docs/skills/`](docs/skills/) — task-specific recipes (charts, metrics, data loading, UI page, testing)
- [`CLAUDE.md`](CLAUDE.md) — Claude-specific guidance (mirror of `agents.md` essentials)

## Tests

```bash
pytest tests/
# with coverage:
pytest --cov=gym_pledge.data --cov=gym_pledge.config tests/
```

Coverage floor: **75 %** on `gym_pledge/data/*` and `gym_pledge/config/*`. UI render functions are not held to this floor — their pure data helpers are.

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
- `gym_pledge/ui/common.py`: shared chart factories (see [ADR 0005](docs/adr/0005-unified-dark-visual-language.md))
- `gym_pledge/data/source.py`: Google Sheets I/O, dedupe, column derivation
- `gym_pledge/data/metrics.py`: pure analytical functions (leaderboard, streaks, lazy logger, frontload/cram)
- `gym_pledge/config/globals.py`: spreadsheet IDs, cutoff, per-month overrides
- `gym_pledge/app_time.py`: timezone-aware "now" / "today" (see [ADR 0004](docs/adr/0004-timezone-via-app-time.md))
- `gym_pledge/styles/theme.css`: app styling
- `gym_pledge/00_Archive/`: read-only history (see [ADR 0006](docs/adr/0006-archive-folder-policy.md))
