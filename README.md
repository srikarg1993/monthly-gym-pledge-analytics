# Monthly Gym Pledge Analytics

[![ci](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/ci.yml)
[![codeql](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/srikarg1993/monthly-gym-pledge-analytics/actions/workflows/codeql.yml)
[![python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![license: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Streamlit dashboard for a monthly fitness pledge, backed by a Google Form and Google Sheet.

> AI agents working on this repo: read [`agents.md`](agents.md) first. It captures the project's hard rules, layering, visual design language, and skill index.

## Features
- Sidebar navigation: About us, Leaderboard, Scorecard, Fitness Yearbook, Log Your Workout
- Leaderboard for the current month with active-user backfill
- Scorecard with modernized charts: qualifying progress ladder, cumulative calorie race, weekday cadence radar, longest streak heartbeat, Brick by Brick vs All-Nighter split, Lazy Logger bubble clusters
- Fitness Yearbook (year calendar heatmap + monthly Altair breakdown, tabbed for mobile)
- Workout logging CTA that embeds the Google Form (with a fallback link)

## Privacy model

This is a **single private friend group's** dashboard, **not** a public service.
There is no auth gate. The deployment URL is shared only with the participants
and security relies on URL obscurity. See
[ADR 0010](docs/adr/0010-privacy-posture.md) for the full posture and threat
model. If you fork this for a different group, **decide your own privacy
posture before pointing it at production data**.

## Documentation

- [`agents.md`](agents.md) — system prompt for any AI agent
- [`docs/adr/`](docs/adr/) — Architectural Decision Records
- [`docs/skills/`](docs/skills/) — task-specific recipes (charts, metrics, data loading, UI page, testing)
- [`CLAUDE.md`](CLAUDE.md) — stub that redirects Claude Code to `agents.md`

## Tests

```bash
python -m pytest tests/
# with coverage:
python -m pytest --cov=gym_pledge.data --cov=gym_pledge.config tests/
```

Coverage floor: **75 %** on `gym_pledge/data/*` and `gym_pledge/config/*`. UI render functions are not held to this floor — their pure data helpers are.

## Setup
1) Install dependencies (uv is the project standard):

```bash
uv pip install -r requirements-dev.txt
```

App-only deployments can use `uv pip install -r requirements.txt`.

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
private_key = "<PASTE PEM-FORMATTED PRIVATE KEY HERE, INCLUDING BEGIN/END LINES>"
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

### Timezone configuration

All "now" / "today" decisions in the app are routed through
`gym_pledge/app_time.py` and obey the `APP_TIMEZONE` environment variable
(IANA name; default `America/Chicago`). Set it in Streamlit Cloud secrets
or your shell to match the participant group's local time:

```bash
export APP_TIMEZONE="America/Los_Angeles"
```

See [ADR 0004](docs/adr/0004-timezone-via-app-time.md) for the rationale.

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
