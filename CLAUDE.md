# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project overview

**monthly-gym-pledge-analytics** is a Streamlit dashboard for a monthly group fitness pledge. Participants log workouts via a Google Form; responses land in a Google Sheet. The app reads the sheet and renders progress dashboards: a monthly leaderboard, per-person scorecards, a full-year calendar heatmap, month-over-month trends, and a CTA to log a workout.

## Tech stack

- Python 3.11
- Streamlit (UI)
- pandas / numpy / altair / matplotlib / seaborn (data + charts)
- gspread + google-auth (Google Sheets access)
- pytest (tests)

## Repository layout

```
gym_pledge/
  dashboard.py            # App shell, sidebar nav, data orchestration
  app_time.py             # Timezone-aware now/today helpers (APP_TIMEZONE)
  config/globals.py       # Sheet IDs, winner cutoffs, per-month overrides
  data/
    source.py             # Google Sheets reader, clean(), get_data(), get_users()
    metrics.py            # Leaderboard + derived stats (streaks, cram/frontload, etc.)
  ui/
    leaderboard.py        # Current-month leaderboard page
    scorecard.py          # Per-person scorecard
    yearcalendar.py       # Year heatmap / breakdown
    monthovermonth.py     # Trend view (hidden from sidebar)
    personalization.py    # Personalization page (hidden from sidebar)
    logyourworkout.py     # Link out to the Google Form
    about.py              # Static About page
    common.py             # Shared UI helpers
  styles/theme.css        # Global dark-theme CSS
  .streamlit/
    config.toml           # Streamlit dark theme
    secrets.toml          # GCP service account JSON (not committed)
tests/                    # pytest suite
start-app.sh              # Convenience launcher (kills port 8501, runs streamlit)
requirements.txt
.devcontainer/            # Python 3.11 dev container, auto-starts the app
```

## Running the app

```bash
pip install -r requirements.txt
streamlit run gym_pledge/dashboard.py
# or
./start-app.sh
```

The dev container auto-starts the app on port 8501 with CORS/XSRF disabled.

## Running tests

```bash
pytest tests/
```

Tests insert `gym_pledge/` onto `sys.path` themselves — no install step required.

## Key domain concepts

- **Workout row** (after `data.source.clean`): `name`, `timestamp`, `workout_date`, `burnt_250` (bool), `month` (YYYY-MM or `pd.NA` for unparseable dates), `dow`, `dom`, `log_delay_days`, `any_workout`. Deduped per `(name, workout_date)` keeping the latest timestamp (`ascending=True` sort + `keep="last"`).
- **Winner cutoff**: `WINNER_CUTOFF = 16` by default, overridable per month via `WINNER_CUTOFF_BY_MONTH` in `gym_pledge/config/globals.py`. Resolve with `winner_cutoff_for_month(month_str)`.
- **Leaderboard row** (`metrics.month_leaderboard`): `workout_days`, `qualifying_days`, `workouts_left`, `is_winner`, `progress`, `rank`.
- **Frontload / cram table** (`metrics.frontload_vs_cram`): includes every `name` in `df_month`, not just qualifying ones — users with zero qualifying workouts appear with style `"No qualifying"` and zero counts.
- **Active users**: pulled from the `Venmo Tracker` worksheet — whoever has `"In"` under the month's column. Used to seed the leaderboard so absent participants still appear with zeros.
- **App timezone**: controlled by `APP_TIMEZONE` env var (default `America/Chicago`). All "current month / today" decisions go through `app_time.py` — do not call `datetime.now()` directly.

## Caching

`data.source.read_google_sheet_as_df`, `get_users`, and `get_data` are all wrapped with `@st.cache_data(ttl=60)`. Every Streamlit rerun reuses the cached DataFrame for up to 60 seconds. To see a fresh workout submission sooner, call `st.cache_data.clear()` or click the Streamlit "Clear cache" menu item.

## Configuration

- `gym_pledge/config/globals.py` — spreadsheet ID, worksheet names, cutoff values.
- `gym_pledge/.streamlit/secrets.toml` — GCP service-account credentials. Not committed; populate manually.
- `APP_TIMEZONE` env var — timezone for "now".

## Conventions

- Changes to data transformations should be covered in `tests/test_metrics.py` or `tests/test_source.py`.
- Per-month cutoff changes go in `WINNER_CUTOFF_BY_MONTH`, not inline.
- UI pages live under `gym_pledge/ui/` and are wired into the sidebar in `dashboard.py`.
- There is currently no linter/formatter config — follow PEP 8, keep imports grouped stdlib / third-party / local.

## Visual design language

All scorecard charts share a unified dark visual language defined in `gym_pledge/ui/common.py`. New charts should follow it:

- **Background**: `#0B1220` (set on `.properties(background=...)` and `configure_view(fill=...)`).
- **Accent palette**:
  - Mint `#5FE1C7` (dark `#1F8C7A`) — winners, candidate, "on it", first half / Brick by Brick, front-loader.
  - Coral `#FFB57A` (dark `#C77744`) — group, in-progress, "catching up", second half / All-Nighter.
  - Cool blue `#9DCEFF` — neutral markers, balanced style.
  - Raspberry `#F47A8E` — falling behind, crammer.
- **Glow stack**: Bars/lines get a wider semi-transparent underlay in the darker shade, with a crisp narrower mark in the bright accent on top. Dots use a halo + core pair.
- **Label "chip" effect**: Render a dark stroke-only mark first (`color="#0B1220" stroke="#0B1220" strokeWidth=4 strokeOpacity=0.9`), then the colored fill mark on top with no stroke. Don't combine fill+stroke on one mark — Vega-Lite paints the stroke over the fill and small text becomes muddy.
- **Medal emojis** 🥇🥈🥉 prepended to the top three rows on ranked charts.
- **Lazy Logger zones** are defined as 6-tuples `(zone_id, label, headline, subtitle, color, icon)` in `LAZY_ZONES`. SVG bubbles use `<radialGradient>` + `<feGaussianBlur>` glow filter.
