# agents.md

System prompt for any AI agent operating on **monthly-gym-pledge-analytics**.
Read this file first. It captures the implicit rules, conventions, and architectural
boundaries the human maintainer expects every contribution to respect.

---

## 1. Project at a glance

- **What it is**: A Streamlit dashboard for a monthly group fitness pledge.
  Participants log workouts via a Google Form; responses land in a Google Sheet.
  The app reads the sheet and renders progress dashboards.
- **Audience**: A small private friend group. There is no public deployment.
- **Stack**: Python 3.11 · Streamlit · pandas / numpy · Altair · matplotlib · seaborn
  · gspread + google-auth · pytest · ruff · pre-commit.
- **Tooling**: `uv` for dependency management. Local `.venv/` lives at repo root.
- **CI**: GitHub Actions (`.github/workflows/ci.yml`) runs ruff + pytest on push.
- **CD**: Streamlit Community Cloud auto-deploys `main` to
  https://pledge2fit.streamlit.app/. Secrets are mirrored in the Streamlit
  Cloud app settings. **Any push to `main` ships to users** — gate via PR.

---

## 2. Repository topology

```
gym_pledge/
  dashboard.py              App shell + sidebar nav (entry point)
  app_time.py               Timezone-aware now/today (APP_TIMEZONE env)
  config/globals.py         Sheet IDs, cutoff, per-month overrides
  data/
    source.py               Google Sheets I/O, clean(), get_data(), get_users()
    metrics.py              Pure analytical functions (leaderboard, streaks, etc.)
  ui/
    common.py               Shared chart factories & UI helpers (~2.7k LOC)
    leaderboard.py          Current-month leaderboard page
    scorecard.py            Per-person scorecard
    yearcalendar.py         Year heatmap / breakdown
    monthovermonth.py       Trends (hidden)
    personalization.py      Personalization (hidden)
    logyourworkout.py       Form CTA
    about.py                Static About page
  styles/theme.css          Global dark-theme CSS
  .streamlit/               config.toml + secrets.toml (secrets gitignored)
tests/                      pytest suite — see SKILLS section below
docs/adr/                   Architectural Decision Records
```

`gym_pledge/00_Archive/` contains historical scaffolding. **Treat archive as
read-only**; do not import from it, do not refactor it, do not delete it without
an explicit ADR.

---

## 3. Architectural boundaries (hard rules)

1. **Layering is strict**: `dashboard.py` → `ui/*` → `data/*` → `config/*`.
   Lower layers may not import from higher ones. `data/*` must never import
   `streamlit` for UI rendering — it may use `@st.cache_data` only.
2. **All "now/today" decisions go through `app_time.py`**. Never call
   `datetime.now()` / `date.today()` directly in app code. Tests may use fixed
   dates.
3. **Per-month cutoff overrides go in `WINNER_CUTOFF_BY_MONTH`** in
   `config/globals.py`. Never inline a cutoff number in metrics or UI code.
   Always resolve via `winner_cutoff_for_month(month_str)`.
4. **Secrets live only in `.streamlit/secrets.toml`** (gitignored) and are
   accessed via `st.secrets["gcp_service_account"]`. Never accept credentials
   as function arguments, never log them, never write them to disk.
5. **DataFrames are immutable from the caller's perspective**. Every function
   in `data/*` and `ui/common.py` that transforms a DataFrame must `.copy()`
   before mutating and return a new DataFrame.
6. **Charts live in `ui/common.py`**. UI page modules orchestrate layout +
   call chart factories; they should not define new Altair specs inline beyond
   trivial wrappers.

---

## 4. Coding conventions

### Style
- **Formatter / linter**: `ruff` (config in `pyproject.toml`). Run
  `ruff check .` and `ruff format .` before committing.
- **Imports**: stdlib → third-party → local, separated by blank lines. `ruff`
  enforces this via the `I` ruleset.
- **Naming**: `snake_case` functions/vars, `PascalCase` classes,
  `UPPER_SNAKE_CASE` constants, `_leading_underscore` for module-private.
- **Type hints**: required on all new public functions in `data/*` and on any
  function added to `ui/common.py`. Use `from __future__ import annotations`
  if forward refs are needed; otherwise use built-in generics (`list[str]`,
  `dict[str, int]`, `X | None`).

### Functional patterns
- Prefer pure functions in `data/metrics.py`. Same input → same output, no
  side effects, no global mutation.
- Prefer comprehensions / pandas vectorization over imperative `for` loops
  when computing derived columns. Loops are fine for short, readable date
  arithmetic (e.g., `longest_streak`).
- No mutable default arguments (`def f(x=[])` is forbidden).
- Error handling: catch `Exception` at I/O boundaries (`data/source.py`),
  surface via `st.warning` / `st.exception` / `st.stop()`. Do **not** wrap
  pure analytical functions in `try/except` — let them raise.

### Idempotency
- Every function in `data/*` must be idempotent: calling it twice on the same
  input yields the same output. Confirmed for `clean`, `get_data`,
  `month_leaderboard`, `lazy_logger_score`, `frontload_vs_cram`. New
  data-layer functions inherit this expectation.
- The `clean` dedupe step relies on a deterministic sort
  (`ascending=True` by timestamp, then `keep="last"`); preserve that order.

### Caching
- `read_google_sheet_as_df`, `get_users`, `get_data` are wrapped with
  `@st.cache_data(ttl=60, show_spinner=False)`. Do not change the TTL without
  an ADR. To force a fresh read in dev, call `st.cache_data.clear()`.

---

## 5. Visual design language

All scorecard charts share a unified dark visual language defined in
`gym_pledge/ui/common.py`. New charts must follow it.

- **Background**: `#0B1220` (set on `.properties(background=...)` and
  `configure_view(fill=...)`).
- **Accent palette**:
  | Role | Bright | Dark glow |
  |------|--------|-----------|
  | Winners / candidate / "On It" / first-half / front-loader | `#5FE1C7` mint | `#1F8C7A` |
  | Group / in-progress / "Catching Up" / second-half / All-Nighter | `#FFB57A` coral | `#C77744` |
  | Neutral markers / Balanced style | `#9DCEFF` cool blue | — |
  | Falling behind / Crammer | `#F47A8E` raspberry | — |
- **Glow stack**: bars/lines get a wider semi-transparent underlay in the
  darker shade, with a crisp narrower mark in the bright accent on top.
  Dots use a halo + core pair.
- **Label "chip" effect**: render a dark stroke-only mark first
  (`color="#0B1220" stroke="#0B1220" strokeWidth=4 strokeOpacity=0.9`),
  then the colored fill mark on top with no stroke. Never combine fill+stroke
  on a single text mark — Vega-Lite paints the stroke over the fill and small
  text becomes muddy.
- **Medal emojis** 🥇🥈🥉 prepended to the top three rows on ranked charts.
- **Lazy Logger zones** are 6-tuples `(zone_id, label, headline, subtitle,
  color, icon)` in `LAZY_ZONES`. SVG bubbles use `<radialGradient>` +
  `<feGaussianBlur>` glow filter.

---

## 6. Domain model

A single **workout row** (post-`clean`) carries:

| Field | Type | Notes |
|-------|------|-------|
| `name` | str | Participant display name |
| `timestamp` | datetime | Form submission time |
| `workout_date` | date | Date the workout actually occurred |
| `burnt_250` | bool | Did the participant burn ≥ 250 cal? |
| `month` | str \| `pd.NA` | `YYYY-MM`; NA for unparseable dates |
| `dow`, `dom` | int | Day-of-week, day-of-month |
| `log_delay_days` | float | `timestamp.date - workout_date` |
| `any_workout` | bool | Always `True` post-clean |
| `calories_burned` | int | When present |

Deduped per `(name, workout_date)` keeping the latest timestamp.

A **leaderboard row** (`metrics.month_leaderboard`) carries:
`name, workout_days, qualifying_days, total_calories, workouts_left,
is_winner, progress, rank`.

The **active-users seed** (`data.source.get_users`) reads the
`Venmo Tracker` worksheet — whoever has `"In"` under the month's column shows
up on the leaderboard with zeros if they have no workouts yet.

---

## 7. Skills index

Domain-specific recipes live in `docs/skills/`. Pick the one that matches
the task before improvising:

- `docs/skills/charts.md` — adding or modifying an Altair chart in `common.py`.
- `docs/skills/metrics.md` — adding a new analytical function in `data/metrics.py`.
- `docs/skills/data-loading.md` — touching Google Sheets I/O, caching, or `clean()`.
- `docs/skills/ui-page.md` — adding a new sidebar page.
- `docs/skills/testing.md` — writing tests, fixtures, and coverage expectations.
- `docs/skills/mutation-testing.md` — finding fake-green tests with mutmut.
- `docs/skills/commit-messages.md` — writing high-signal git commit messages.
- `docs/skills/ci-workflows.md` — adding or modifying GitHub Actions workflows.

---

## 8. Test discipline

- `pytest tests/` is the canonical command. Tests insert `gym_pledge/` onto
  `sys.path` themselves; no install step required.
- Coverage floor: **75%** on `data/*` and `config/*`. Measure with
  `pytest --cov=gym_pledge.data --cov=gym_pledge.config tests/`.
  UI render functions are not held to this floor.
- Every new function in `data/*` must ship with at least one happy-path test
  and one edge-case test (empty input, missing column, etc.).
- Per-month cutoff changes must be covered in `tests/test_cutoff_config.py`.

---

## 9. Workflow expectations for AI agents

1. **Read this file, then any `docs/skills/*.md` matching the task.**
2. **Plan before editing.** Use a todo list for any multi-step task.
3. **Run tests + ruff after every meaningful change.**
   `python -m pytest tests/ -q && ruff check .`
4. **Never commit** `.streamlit/secrets.toml`, `.venv/`, or anything matching
   `.gitignore`.
5. **Architectural changes require an ADR** in `docs/adr/` using the existing
   numbered template. The ADR is part of the PR.
6. **Don't break what works.** When the user says "this looks good", treat
   that surface as locked. Modernization passes operate one chart at a time
   with tests + lint between each.
7. **No silent failures.** If a transformation can't proceed (missing column,
   empty DataFrame, bad timezone), surface it via `st.warning` /
   `st.error` / `st.stop()` at the UI boundary, or `raise` in pure code.
8. **Don't add features that weren't asked for.** This includes docstrings,
   comments, and helper abstractions on code you didn't otherwise change.

---

## 10. Mandatory parallel-work + pre-commit gate

These rules apply to **every** AI agent working in this repo. Non-negotiable.

### Parallelize aggressively
- Prefer **subagents** (e.g. an `Explore` agent) for any task with
  independent sub-parts. One subagent per audit dimension.
- When tools are independent (search + fetch + read), call them in a
  **single** parallel tool block — never one after the other.
- Linear sequences of `read_file` / `grep_search` calls are a smell;
  combine or hand off to a subagent.

### Pre-commit gate (run before EVERY commit + push)
Fan out the following in parallel — usually one subagent per item — and only
commit after all four pass:

1. **Format / lint sweep** — `ruff format .` + `ruff check .` over the whole
   repo (not just changed files).
2. **Code quality audit** — review changed files for missing docstrings on
   new public functions, missing type hints in `data/*` and `ui/common.py`,
   non-obvious magic numbers without inline comments, and missing error
   handling at I/O boundaries.
3. **Logic-error audit** — read the diff for off-by-ones, wrong-sign bugs,
   timezone mishandling, missing edge cases (empty df, NaN, future dates,
   negative numbers, boundary values), and inconsistent state between
   related fields (e.g. a bool that disagrees with the number it summarizes).
4. **Doc/skill update audit** — check whether the change warrants:
   - new/updated `docs/skills/*.md`
   - new ADR in `docs/adr/` (architectural decisions)
   - update to `agents.md` / `CLAUDE.md` (convention changes)
   - update to `README.md` (user-visible behavior changes)

### CI verification after push
- Use [`scripts/ci-status.ps1`](scripts/ci-status.ps1) (requires `gh` CLI)
  or `gh run list --branch <b>` to verify CI is green. Don't assume.
- If `gh` isn't authed yet, fetch the Actions web page directly.
