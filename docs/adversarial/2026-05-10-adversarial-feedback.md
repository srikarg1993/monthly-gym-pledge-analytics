# Adversarial Feedback - 2026-05-10

This is a deliberately harsh review of the repo as it exists on 2026-05-10.
The goal is not to be polite. The goal is to make the next developer agent
raise the floor until this looks like a production-grade app instead of a
well-liked private Streamlit dashboard with several sharp edges.

Known backlog items in `docs/backlog.md` are not re-scored as new findings
unless they create direct evidence in the current source. In particular, the
known leaked historical GCP key rotation item is not counted again here, but it
still affects the security posture until completed.

## Verification Performed

- Read project instructions in `agents.md`.
- Read repo skill docs for data loading, metrics, charts, UI pages, testing,
  repo hygiene, and CI workflows.
- Reviewed core app files:
  - `gym_pledge/dashboard.py`
  - `gym_pledge/app_time.py`
  - `gym_pledge/config/globals.py`
  - `gym_pledge/data/source.py`
  - `gym_pledge/data/metrics.py`
  - `gym_pledge/ui/*.py`
  - `gym_pledge/ui/common.py`
  - `gym_pledge/styles/theme.css`
- Reviewed tests, hooks, workflows, dependency files, README, gitignore,
  devcontainer, and helper scripts.
- Ran:
  - `.\\.venv\\Scripts\\python.exe -m pytest tests/ -q`
  - `.\\.venv\\Scripts\\ruff.exe check .`
  - `.\\.venv\\Scripts\\ruff.exe format --check .`
  - `git status --short`
  - `git diff --stat`
  - `git status --ignored --short`

Current checks pass:

- Tests: pass, with reported data/config coverage at 77.41%.
- Ruff lint: pass.
- Ruff format check: pass.
- Working tree before writing this report: clean.

Passing checks are not the same thing as production readiness.

## Ratings

Scale: 1 = weak, 3 = acceptable for a private hobby app, 5 = production-grade.

| Category | Rating | Rationale |
|---|---:|---|
| Domain correctness | 2.5 / 5 | Core metrics mostly work, but there are rule contradictions, roster fallbacks, same-day calorie ambiguity, and data quality blind spots. |
| Data ingestion and schema resilience | 2.0 / 5 | `clean()` is better than a notebook script, but row drops are silent, schema drift is handled late, and source coverage is only 61%. |
| Test adequacy | 2.5 / 5 | Useful unit tests exist, including edge cases, but they mostly test pure helpers. No Streamlit smoke, no UI regression, weak I/O boundary coverage, and some fixtures violate the documented post-clean domain model. |
| CI and hooks | 3.5 / 5 | CI, pre-commit, CodeQL, Dependabot, and junk blocking exist. Missing type checks, dependency security audit, smoke test, and stronger supply-chain posture. |
| Security | 2.0 / 5 | Unsafe HTML from sheet values, external scripts/forms, no app-level auth, and known historical secret exposure. Private audience lowers risk but does not remove it. |
| UI polish | 2.0 / 5 | The app has energy, but too much custom chrome, inconsistent visual language, heavy gradients, copy that sounds casual, brittle CSS, and cramped dense views keep it from feeling professional. |
| Accessibility | 1.5 / 5 | Heavy custom HTML/CSS, color-dependent status, fixed embeds, no keyboard/focus strategy, no contrast audit, no screen-reader story. |
| Performance | 3.0 / 5 | Fine for a friend group, but imports, chart recomputation, full-sheet reads, Matplotlib lifecycle, and CDN/render work are not engineered. |
| Maintainability | 2.75 / 5 | ADRs and skills are strong, but `ui/common.py` is too large, hidden pages and old helpers remain, and config/copy drift exists. |
| Production operations | 2.25 / 5 | CI/CD basics exist, but no health checks, observability, access gate, data-quality report, or rollback/snapshot path in code. |
| Documentation accuracy | 3.0 / 5 | The docs are unusually good for a small app, but several docs contradict the actual code and setup commands. |
| Overall | 2.6 / 5 | Good private dashboard foundation. Not production-level yet. The biggest gap is not lint; it is untested runtime behavior and inconsistent product rules. |

## Executive Verdict

This repo is far above "random Streamlit notebook" quality. It has structure,
ADRs, tests, pinned dependencies, pre-commit, CI, CodeQL, and clear agent
instructions. That is the good news.

The bad news: the app still relies on private-group trust and human tolerance.
Several user-visible claims are not guaranteed by the data pipeline. Several
failures silently degrade into misleading output. The UI is customized enough
to be fragile but not disciplined enough to feel polished. The test suite
proves a subset of pure helper behavior, not that the shipped app works.

If the bar is "masterclass production level", the next phase should be:

1. Freeze the domain rules in code and tests.
2. Add data-quality reporting instead of silent drops.
3. Remove unsafe raw HTML or escape every dynamic value.
4. Add Streamlit smoke and visual regression checks.
5. Consolidate design language and stop styling Streamlit internals globally.
6. Turn operational assumptions into validated config.

## P0 Findings

### P0-01: Same-day calorie combination is contradicted by the pipeline

Evidence:

- `gym_pledge/data/source.py:232` dedupes by `(name, workout_date)` and keeps
  only the latest timestamp.
- `gym_pledge/ui/about.py:517` tells users: "Multiple workouts on the same day
  can be combined to cross 250+ calories."

Why this is bad:

If a user logs 150 calories at lunch and 150 calories at night, the current
dedupe rule can discard one entry and leave only one 150-calorie row. The app
copy says the day qualifies; the code can say it does not. That is not a UI
wording issue. That is a broken domain contract.

Recommendation:

- Pick one rule and enforce it everywhere.
- If same-day combination is real, change clean-time dedupe to aggregate all
  rows per `(name, workout_date)`:
  - latest timestamp for `timestamp`
  - sum calories for `calories_burned`
  - derive `burnt_250` from summed calories when any calorie value exists
  - preserve a count/list of source submissions for auditability
- Add tests for:
  - two sub-250 logs summing to >= 250
  - latest timestamp retained
  - mixed blank calorie and checkbox rows
  - duplicate exact rows
- If same-day combination is not real, remove the About page claim.

### P0-02: Dynamic HTML from sheet data is not escaped

Evidence:

- `gym_pledge/ui/common.py:64` and `gym_pledge/ui/common.py:74` concatenate
  table headers and cell values into HTML.
- `gym_pledge/ui/common.py:1844` injects participant names into podium HTML.
- `gym_pledge/ui/common.py:2499` and `gym_pledge/ui/common.py:2515` inject
  names and SVG title values into raw SVG/HTML.
- `gym_pledge/ui/yearcalendar.py:223`, `gym_pledge/ui/about.py`, and other
  modules render many blocks with `unsafe_allow_html=True`.

Why this is bad:

This app treats Google Sheet values as trusted HTML. In a private group that
may feel acceptable until someone enters a name like `<img onerror=...>`.
Streamlit's markdown sanitizer is not a substitute for escaping dynamic text
before raw HTML injection.

Recommendation:

- For all dynamic strings rendered through raw HTML/SVG, use `html.escape`.
- Prefer native `st.dataframe` or `st.data_editor` for tables.
- Add tests that pass hostile names and assert the generated HTML contains
  escaped text, not raw tags.
- Centralize HTML rendering helpers so escaping is default and opt-out is rare.

### P0-03: Static pages are blocked by Google Sheets failures

Evidence:

- `gym_pledge/dashboard.py:108` calls `get_data()` before routing.
- `gym_pledge/dashboard.py:156` to `gym_pledge/dashboard.py:169` routes after
  the sheet read.

Why this is bad:

If Google Sheets, credentials, or schema cleaning fails, even "About us" and
"Log Your Workout" cannot render. That is a brittle app shell. A static form
CTA should not depend on the analytics backend being healthy.

Recommendation:

- Route first.
- Only data-load pages that need analytics.
- Let `About us` and `Log Your Workout` render independently.
- Add a Streamlit smoke test or import-level test that simulates data-source
  failure and verifies static pages remain reachable.

### P0-04: Missing active-user month columns silently turn into "everyone"

Evidence:

- `gym_pledge/data/source.py:66` filters users only if the month label exists.
- If the month label is missing, the function returns all names from the
  tracker instead of warning or failing.

Why this is bad:

The current-month leaderboard can include people who are not actually "In" for
the month. This is a silent trust violation. The app looks confident while the
roster filter is not applied.

Recommendation:

- If `month_str` is passed and the derived month label is missing, return an
  explicit error state or empty list with a visible warning.
- Distinguish "could not read roster", "month column missing", and "no active
  users" instead of returning `None` for all of them.
- Add tests for `get_users()` with:
  - present month column
  - missing month column
  - empty users sheet
  - missing name column
  - duplicated users

## P1 Domain and Logic Findings

### P1-01: Domain docs say `dow` is int, code stores day name string

Evidence:

- `agents.md` domain model says `dow`, `dom` are int.
- `gym_pledge/data/source.py:245` sets `dow` to `.dt.day_name()`, a string.

Impact:

Agents and tests can build the wrong fixtures. Future metrics may assume
integer weekday values and break or silently sort weekdays alphabetically.

Recommendation:

- Decide whether `dow` is integer or string.
- If string is desired, update `agents.md`.
- If int is desired, store `dow` as `dt.dayofweek` and add `weekday_name` for
  display.

### P1-02: `calories_met_250` lies for blank calorie rows

Evidence:

- `gym_pledge/data/source.py:227` sets `calories_met_250 = calories_burned >=
  250`.
- For blank calories, pandas comparison produces `False`, while `burnt_250`
  can still be `True` from the checkbox.

Impact:

Downstream code can see a row where `burnt_250 == True` and
`calories_met_250 == False` even though the numeric calorie field was missing,
not below threshold.

Recommendation:

- Set `calories_met_250` to `pd.NA` where calories are missing.
- Treat it as "numeric calorie evidence met the target", not as the canonical
  qualification flag.
- Add a test for blank calories plus checked form bool.

### P1-03: Ranking is too shallow for an actual leaderboard

Evidence:

- `gym_pledge/data/metrics.py:42` ranks only by `qualifying_days`.
- `gym_pledge/data/metrics.py:45` sorts by `qualifying_days` and `name`.

Impact:

Two users with the same qualifying days but very different workout days or
calories get the same rank and then alphabetical ordering. Alphabetical tie
breakers are arbitrary and can look unfair.

Recommendation:

- Define rank semantics explicitly:
  - competition rank by qualifying days only, or
  - display rank by qualifying days, workout days, total calories, name
- If tie groups are intentional, label them as ties.
- Add tests for tie behavior.

### P1-04: Roster names and form names are normalized differently

Evidence:

- `clean()` normalizes whitespace in form names at
  `gym_pledge/data/source.py:152`.
- `get_users()` only strips names at `gym_pledge/data/source.py:73`.

Impact:

Case differences, repeated spaces, or aliases can split one person into two
leaderboard rows or fail to join roster activity to workout rows.

Recommendation:

- Create a single `normalize_name()` helper used by both sheet readers.
- Add optional alias mapping for real group-name drift.
- Add tests for case, whitespace, and duplicate roster names.

### P1-05: Silent row drops hide data-quality problems

Evidence:

- `clean()` drops bad timestamps, bad dates, future dates, old dates,
  out-of-range calories, and impossible date rows without returning a report.

Impact:

The app can quietly undercount a participant. That is worse than failing,
because users will trust a polished wrong leaderboard.

Recommendation:

- Return `(clean_df, quality_report)` from a lower-level cleaner, or attach a
  report object to the UI boundary.
- Show admin-only or expander-visible counts:
  - rows read
  - rows kept
  - rows dropped by reason
  - suspicious but retained rows
- Add tests for the report counts.

### P1-06: The app uses one-day future grace that can create negative delays

Evidence:

- `gym_pledge/data/source.py:199` allows `workout_date` up to one day after
  `timestamp_date`.
- `gym_pledge/data/source.py:248` computes delay as `timestamp_date -
  workout_date`.

Impact:

Rows can survive with `log_delay_days == -1`. Lazy Logger can then reward
"early logging" or skew averages.

Recommendation:

- Parse and localize timestamps to the app timezone before comparing dates.
- If a row is retained due timezone grace, normalize it to same-day delay or
  add an explicit "timezone adjusted" reason.
- Add a test for timezone-boundary submissions.

### P1-07: `get_users()` uses `None` for multiple different failure modes

Evidence:

- Read failure, empty sheet, missing name column, and no users after filtering
  all return `None` in `gym_pledge/data/source.py:50`.

Impact:

Callers cannot tell whether they should fallback, stop, warn, or show an empty
month. `users or None` in `dashboard.py:146` erases the difference.

Recommendation:

- Return a typed result object:
  - `users: list[str]`
  - `status: ok | missing_column | empty | read_error | no_active_users`
  - `message: str`
- Stop silently falling back to workout-only leaderboards when roster reads
  fail.

### P1-08: Scorecard claims winners burned 4000+ calories regardless of data

Evidence:

- `gym_pledge/ui/scorecard.py:445` says every winner burned 4000+ calories.

Impact:

This is mathematically true only if cutoff is 16 and every qualifying day is
based on 250 calories. The app supports per-month cutoff overrides and
checkbox-only rows without numeric calories. The claim can be false.

Recommendation:

- Replace with "reached the monthly qualifying target."
- If a calorie claim is shown, compute `cutoff * 250` for the selected month
  and only show it when the month has reliable calorie data.

### P1-09: About page hard-codes business rules

Evidence:

- `gym_pledge/ui/about.py:4` to `gym_pledge/ui/about.py:6` define pledge
  amount, qualifying days, and calorie target separately from config.

Impact:

February override says 15 in config, but About still says 16. A future cutoff
change can update the metrics and leave the rules page wrong.

Recommendation:

- Move business-rule constants to config.
- Render the default cutoff plus a clear note for per-month overrides.
- Add a test or lightweight assertion that About constants match config.

### P1-10: Hidden pages are imported but unreachable by sidebar

Evidence:

- `dashboard.py` imports `monthovermonth` and `personalization`.
- Routing supports `"Month-over-month Trends"` and `"Personalization"`.
- Sidebar buttons never set those tab values.

Impact:

Code exists without an obvious user path. Tests and maintainers may assume
features are live because README mentions month-over-month trends.

Recommendation:

- Either expose the pages, delete them, or document them as deep-link/internal.
- Add query-param routing if hidden routes are intentional.

### P1-11: Devcontainer disables CORS and XSRF protection

Evidence:

- `.devcontainer/devcontainer.json:22` starts Streamlit with
  `--server.enableCORS false --server.enableXsrfProtection false`.

Impact:

It is "only dev", but it normalizes unsafe flags in the standard cloud dev
environment.

Recommendation:

- Remove those flags unless there is a documented local-preview requirement.
- If needed, add a comment explaining why they are safe in this context and
  never used in deployment.

### P1-12: External ApexCharts CDN can silently break Yearbook charting

Evidence:

- `gym_pledge/ui/yearcalendar.py:16` hard-codes jsDelivr ApexCharts.
- `gym_pledge/ui/yearcalendar.py:158` injects the script into a component.

Impact:

If the CDN is blocked or slow, the chart can fail independently of the app.
There is no fallback, no error state, and no test that the chart renders.

Recommendation:

- Prefer Altair for this chart.
- If ApexCharts stays, vendor the JS or provide a table fallback that is
  always visible.
- Add a smoke test that detects component render errors.

## P2 Testing Findings

### P2-01: Source-layer coverage is weak where failure matters most

Evidence:

- Test output reports `gym_pledge/data/source.py` at 61% coverage.
- Uncovered lines include Google Sheets read, `get_users`, and `get_data`
  boundaries.

Impact:

The highest-risk code is I/O, auth, schema drift, and user-visible failures.
That is exactly where coverage is thin.

Recommendation:

- Mock `read_google_sheet_as_df()` and `st` to test `get_users()` and
  `get_data()` behavior.
- Add branch tests for each warning/stop path.
- Raise the data/config coverage floor after closing this gap.

### P2-02: No Streamlit app smoke test

Evidence:

- Tests target pure helpers and data functions.
- No test boots `streamlit run gym_pledge/dashboard.py`.

Impact:

The app can pass tests while failing at runtime because of page config,
imports, CSS/JS injection, widget key collisions, or missing secrets.

Recommendation:

- Add a headless smoke test that starts Streamlit with mocked data and asserts
  the page loads without exception.
- If Playwright is too heavy, start with `streamlit.testing.v1.AppTest` for
  pages that can be isolated.

### P2-03: No visual regression tests

Evidence:

- No Playwright screenshot tests.
- No rendered chart/canvas checks.

Impact:

Most of the app value is visual. The test suite can pass while the UI is blank,
overlapping, clipped, or ugly.

Recommendation:

- Add one desktop and one mobile screenshot smoke for:
  - Leaderboard
  - Scorecard
  - Yearbook
  - Log Your Workout
- Assert no Streamlit error banner and no blank chart containers.

### P2-04: Some metric fixtures violate the documented post-clean model

Evidence:

- `tests/test_metrics.py:20` builds duplicate same-day rows for Ann.
- `tests/test_metrics.py:137` asserts total calories includes both duplicate
  same-day Ann rows.
- The domain model says post-clean data is deduped per `(name, workout_date)`.

Impact:

Tests are validating behavior on data shapes that should not reach metrics.
This makes the suite less authoritative and can bless impossible states.

Recommendation:

- Split tests into:
  - metrics tests with valid post-clean data
  - defensive tests that explicitly document invalid input behavior
- Add a same-day aggregation/dedupe domain test once the rule is resolved.

### P2-05: No tests for HTML escaping or injection safety

Evidence:

- Unsafe HTML is heavily used.
- Tests never pass malicious names or table values.

Impact:

XSS regressions would not be caught.

Recommendation:

- Add unit tests for HTML builders with names like
  `<script>alert(1)</script>`.
- Assert escaped output.
- Prefer native Streamlit renderers.

### P2-06: No tests for dashboard routing and data-loading order

Evidence:

- `dashboard.py` is not tested.

Impact:

The static-page-blocked-by-data failure is invisible to tests.

Recommendation:

- Refactor routing/data loading into small functions and test them.
- Use Streamlit AppTest or monkeypatch `get_data()` to raise and verify static
  pages can still render.

### P2-07: No tests for current-month no-workout roster-only leaderboard

Evidence:

- Tests cover `month_leaderboard(... all_users=[...])`, but not the app-level
  path where the current month has zero workout rows and active roster data.

Impact:

This is a common first-day-of-month state. The app could show no participants
or stale month state.

Recommendation:

- Add an app-level or orchestration test for "current month has roster users
  but no logs yet."

### P2-08: No tests for config/docs consistency

Evidence:

- About page constants are not tested against `config.globals`.
- Agent domain model is not tested against `clean()` output.

Impact:

The repo can document one schema/rule and ship another.

Recommendation:

- Add a small schema contract test for `clean()` output columns and dtypes.
- Add a rules consistency test for visible rule constants.

### P2-09: No package/import test outside sys.path mutation

Evidence:

- Tests insert `gym_pledge/` onto `sys.path`.
- `pyproject.toml` does not define a package install.

Impact:

CI does not prove the project can be installed or imported as a conventional
package. That is acceptable for Streamlit Cloud, but not production-grade.

Recommendation:

- Either keep the flat app layout and document it as intentional, or add real
  package metadata and test `pip install -e .`.

### P2-10: No mutation testing gate despite mutation-test commentary

Evidence:

- Tests mention a mutmut pass in `tests/test_metrics.py:188`, but mutmut is
  not present in dependencies or CI.

Impact:

The comment implies a quality practice that is no longer enforced.

Recommendation:

- Either remove the mutation-test narrative from test comments or add an
  optional documented mutation-testing command.

## P2 CI, Hooks, and Repo Hygiene Findings

### P2-11: CI has no type checking

Evidence:

- `pyproject.toml` configures ruff and pytest only.
- No mypy/pyright job.

Impact:

The codebase has many untyped UI helpers and dynamic dict/DataFrame contracts.
Ruff cannot catch wrong column types, optional `None` misuse, or public
function signature drift.

Recommendation:

- Add pyright or mypy in a gradual mode.
- Start with `data/*`, `config/*`, and pure `_build_*` helpers.

### P2-12: CI has no dependency vulnerability audit

Evidence:

- No `pip-audit`, `uv audit`, Safety, or equivalent in CI.

Impact:

Pinned dependencies can still become vulnerable.

Recommendation:

- Add a scheduled and PR-time dependency audit.
- If noisy, start as non-blocking and graduate to blocking.

### P2-13: CI does not run a deployed-app health check

Evidence:

- No workflow verifies the live Streamlit URL after `main` deploys.

Impact:

CI can be green and Streamlit Cloud can still fail after deployment due
secrets, platform runtime, or app startup issues.

Recommendation:

- Add a post-merge health check that hits the live URL.
- Assert HTTP 200 and absence of common Streamlit error text.

Note: a health-check item exists in backlog. This finding is included because
it directly affects the production-readiness rating, not because it is unknown.

### P2-14: Actions are major-version pinned, not SHA pinned

Evidence:

- `.github/workflows/ci.yml` uses `actions/checkout@v5`,
  `actions/setup-python@v6`, `astral-sh/setup-uv@v7`.

Impact:

This matches the repo convention, but strict production hardening would pin
actions by SHA to reduce supply-chain risk.

Recommendation:

- If production/security posture matters, pin critical actions by SHA and let
  Dependabot update them.
- If major pins are intentionally acceptable, document that tradeoff.

### P2-15: Pre-commit can mutate code but CI only reports after the fact

Evidence:

- `.pre-commit-config.yaml` runs `ruff --fix` and `ruff-format`.
- CI runs pre-commit but cannot push fixes back.

Impact:

Contributors can get red CI for formatting that was automatically fixable.
That is not wrong, but it is friction.

Recommendation:

- Keep as-is for a solo repo, or add a documented `pre-commit run --all-files`
  requirement in PR instructions.
- Do not add an auto-format bot unless you actually want bot commits.

### P2-16: `start-app.sh` kills port 8501 with `kill -9`

Evidence:

- `start-app.sh:12` uses `xargs kill -9`.

Impact:

This is a convenience script, but `kill -9` is a blunt instrument. It can kill
an unrelated process on the port without graceful shutdown.

Recommendation:

- Prompt before killing, use normal `kill` first, then escalate only if still
  running.
- Add a PowerShell equivalent if Windows is a primary dev environment.

### P2-17: Devcontainer setup ignores uv convention

Evidence:

- `.devcontainer/devcontainer.json:20` uses `pip3 install --user`.
- `agents.md` says tooling is `uv`.

Impact:

The documented dev environment and the repo convention diverge.

Recommendation:

- Install uv in the devcontainer and run `uv pip install -r requirements-dev.txt`.
- Avoid separately installing Streamlit outside requirements.

### P2-18: Ignored local junk is extensive

Evidence:

- `git status --ignored --short` shows local caches, pycache directories,
  notebook checkpoints, `.coverage`, and `gym_pledge/.streamlit/secrets.toml`.

Impact:

They are ignored, so this is not a tracked-file issue. But the working tree is
noisy, and prior history already had a cache/secret incident.

Recommendation:

- Periodically clean ignored generated artifacts with a documented safe command.
- Keep `.streamlit/secrets.toml` local but rotate the historical key per
  backlog.

## P2 UI and Product Findings

### P2-19: The UI copy is too casual for a production-quality product

Evidence:

- `gym_pledge/ui/scorecard.py:444` uses "This month's winners!!"
- `gym_pledge/ui/scorecard.py:445` uses "Congratulations guys!!"
- `gym_pledge/dashboard.py:120` says "Monthly Pledge to Fitness " with a
  trailing space and awkward phrasing.

Impact:

This reads like a quick internal app, not a polished product.

Recommendation:

- Use concise, neutral copy:
  - "Monthly Fitness Pledge"
  - "Winners"
  - "Reached the monthly qualifying target"
- Remove double exclamation marks.

### P2-20: The global design language is inconsistent with the repo's own ADR

Evidence:

- `agents.md` defines mint/coral/blue/raspberry accents.
- `gym_pledge/ui/common.py:11` to `gym_pledge/ui/common.py:23` define a
  separate older palette.
- `gym_pledge/ui/scorecard.py:26` to `gym_pledge/ui/scorecard.py:30` define
  another muted palette.
- `gym_pledge/ui/yearcalendar.py:184` uses Apex colors outside the palette.

Impact:

The app does not feel like one designed system. It feels like layers of
modernization passes.

Recommendation:

- Create one `ui/theme.py` or constants block for semantic colors.
- Replace page-local color constants with semantic tokens.
- Add a visual QA checklist for each chart modernization.

### P2-21: CSS globally styles every keyed Streamlit container

Evidence:

- `gym_pledge/styles/theme.css:548` targets `div[class^="st-key-"]`.

Impact:

Any new keyed container becomes a card with padding, border, shadow, and
horizontal scroll. This is a trap for future UI work.

Recommendation:

- Remove the generic keyed-container selector.
- Style only explicit known keys, or wrap custom HTML in explicit classes.

### P2-22: Sidebar active state is unfinished

Evidence:

- `gym_pledge/styles/theme.css:542` says active state will be wired next.
- Sidebar is plain buttons in `dashboard.py:88`.

Impact:

Users cannot reliably see which page they are on from nav styling.

Recommendation:

- Use `st.radio`, `st.segmented_control`, or a native navigation component.
- If buttons remain, inject explicit active classes based on `session_state`.

### P2-23: Sidebar autocollapse script is brittle and may not execute

Evidence:

- `dashboard.py:43` injects a `<script>` through `st.markdown`.
- It queries Streamlit internals and `window.parent.document`.

Impact:

Streamlit DOM changes can break it. Depending on Streamlit behavior, scripts
in markdown may not execute reliably.

Recommendation:

- Prefer native sidebar behavior.
- If custom JS is needed, put it in a `components.html` wrapper and test it
  with a browser smoke test.

### P2-24: Fixed Google Form iframe is not mobile-grade

Evidence:

- `gym_pledge/ui/logyourworkout.py:35` uses a fixed 900x1000 iframe with
  `scrolling=False`.

Impact:

On narrow screens, the form can clip or force awkward horizontal behavior.

Recommendation:

- Use `width="100%"` or omit width where possible.
- Enable scrolling.
- Show a prominent "Open form" link using the existing `WORKOUT_FORM_URL`.

### P2-25: Yearbook is too dense

Evidence:

- `gym_pledge/ui/yearcalendar.py:269` renders monthly breakdown.
- `gym_pledge/ui/yearcalendar.py:289` renders a 12-month calendar grid.

Impact:

Stats, chart, table expander, legend, and 12 calendars on one page overload
the screen, especially mobile.

Recommendation:

- Split Yearbook into tabs:
  - Overview
  - Monthly breakdown
  - Calendar
- Default to the most useful view and let detail be opt-in.

### P2-26: Radar charts can mislead because scales differ

Evidence:

- `gym_pledge/ui/scorecard.py:665` explicitly says each chart auto-scales to
  its own data.
- `gym_pledge/ui/scorecard.py:675` and `gym_pledge/ui/scorecard.py:680`
  render separate figures.

Impact:

The group and participant shapes are visually comparable but use different
radial scales. That is a classic chart honesty problem.

Recommendation:

- Use shared `r_max` when comparing group and participant.
- If readability is the goal, add a toggle: "shared scale" vs "fit each".
- Default to shared scale.

### P2-27: Calendar uses punitive red dots for every missed past day

Evidence:

- `gym_pledge/styles/theme.css:435` styles missed dots red.
- Calendar fills every past no-workout date with a missed marker.

Impact:

The UI becomes noisy and negative. It may obscure the actual signal: workout
and qualifying days.

Recommendation:

- Use muted empty cells by default.
- Only highlight missed days when there is a specific goal-tracking context.

### P2-28: Custom tables are not interactive or accessible enough

Evidence:

- `render_styled_table()` builds static HTML in `gym_pledge/ui/common.py:38`.

Impact:

Users lose sorting, copying, column resizing, keyboard behavior, and native
dataframe affordances.

Recommendation:

- Use `st.dataframe` with `column_config` and container styling.
- Only use custom HTML tables for tiny decorative summaries.

### P2-29: The app overuses explanatory captions

Evidence:

- Scorecard sections repeatedly explain how to read charts in visible copy.

Impact:

A polished operational app should be mostly self-explanatory. The current
copy makes the UI feel like a demo deck.

Recommendation:

- Move explanations into tooltips or help icons.
- Rename charts and axes so less instructional prose is needed.

## P3 Maintainability Findings

### P3-01: `ui/common.py` is doing too much

Evidence:

- `gym_pledge/ui/common.py` contains styling helpers, table rendering,
  Matplotlib helpers, many Altair chart factories, SVG bubble packing, podium
  HTML, and data-shaping helpers.

Impact:

This file is becoming a junk drawer. It discourages focused ownership and
increases merge conflict risk.

Recommendation:

- Split into:
  - `ui/theme.py`
  - `ui/tables.py`
  - `ui/charts/progress.py`
  - `ui/charts/streaks.py`
  - `ui/charts/lazy_logger.py`
  - `ui/charts/calories.py`
- Keep compatibility imports in `ui/common.py` temporarily if needed.

### P3-02: Dead or legacy helpers remain in active code

Evidence:

- `gym_pledge/ui/scorecard.py:390` marks `_build_weekday_mix_df` deprecated.
- `gym_pledge/ui/common.py:799` has a deprecated ignored parameter.

Impact:

Deprecated helpers in active modules invite reuse and confusion.

Recommendation:

- Remove deprecated active-code helpers after confirming tests and imports.
- If backward compatibility is needed, add a removal date/comment.

### P3-03: `SERVICE_ACCOUNT_JSON_PATH` is stale config

Evidence:

- `gym_pledge/config/globals.py:8` defines `SERVICE_ACCOUNT_JSON_PATH`.
- Auth now uses Streamlit secrets in `source.py:25`.

Impact:

Stale config implies a supported code path that no longer exists.

Recommendation:

- Remove the constant.
- Update README text that still implies file-path setup where needed.

### P3-04: `dedupe` variable in dashboard is unused

Evidence:

- `gym_pledge/dashboard.py:100` sets `dedupe = True`.

Impact:

Dead local state suggests a removed UI control and creates false confidence
that dedupe can be configured.

Recommendation:

- Delete the variable.
- If dedupe configurability is desired, thread it into `get_data()` explicitly.

### P3-05: README setup conflicts with repo tooling convention

Evidence:

- `README.md:41` says `pip install -r requirements.txt`.
- `agents.md` says tooling is `uv`.

Impact:

The main public setup path and agent operating rules disagree.

Recommendation:

- Make README use `uv` first.
- Keep a pip fallback if needed.

### P3-06: README coverage command likely does not match import layout

Evidence:

- `README.md:32` says `pytest --cov=gym_pledge.data --cov=gym_pledge.config`.
- `pyproject.toml:45` uses `source = ["data", "config"]` because tests import
  modules after inserting `gym_pledge/` into `sys.path`.

Impact:

Users can run a documented command that reports confusing coverage.

Recommendation:

- Document `python -m pytest` as the canonical coverage command because
  `pyproject.toml` already carries addopts.

### P3-07: About and README feature lists are stale relative to navigation

Evidence:

- README says sidebar navigation includes About, Leaderboard, Scorecard, Log.
- The actual sidebar also includes Fitness Yearbook.
- README mentions month-over-month trends, but no sidebar route exposes it.

Impact:

Docs do not tell a maintainer what is actually live.

Recommendation:

- Update README feature/navigation list.
- Explicitly label hidden pages or expose them.

### P3-08: App timezone default may be wrong for the actual audience

Evidence:

- `gym_pledge/app_time.py:12` defaults to `America/Chicago`.

Impact:

If users are not in Central time, current month/day behavior can flip early or
late. Even if Central is intentional, the reason is not documented in config.

Recommendation:

- Document why `America/Chicago` is the app timezone.
- Add deployment instructions for `APP_TIMEZONE`.
- Add tests for month boundary behavior.

## P3 Security and Privacy Findings

### P3-09: No app-level access control

Evidence:

- The app relies on Streamlit Community Cloud URL access and private group
  obscurity.

Impact:

Anyone with the URL can likely view participant names and workout history.

Recommendation:

- Add a lightweight auth gate:
  - Streamlit auth
  - shared password in secrets
  - Google OAuth allowlist
- At minimum, document the privacy model clearly.

### P3-10: Hard-coded Venmo handle and Google Form URL are privacy-sensitive

Evidence:

- `gym_pledge/ui/about.py:7`
- `gym_pledge/ui/logyourworkout.py:4`

Impact:

These are not secrets, but they are personal identifiers and operational
links. Hard-coding makes it easy to accidentally fork/share them.

Recommendation:

- Move personal/operational links to config or Streamlit secrets.
- Add visible validation if not configured.

### P3-11: `target="_blank"` link lacks `rel="noopener noreferrer"`

Evidence:

- `gym_pledge/ui/about.py:357` opens Venmo in a new tab.

Impact:

This is a minor but standard web hardening issue.

Recommendation:

- Add `rel="noopener noreferrer"` to external links opened in a new tab.

### P3-12: Error UI may expose too much runtime detail

Evidence:

- `gym_pledge/data/source.py:55`, `source.py:263`, and `source.py:270` call
  `st.exception(e)`.

Impact:

In a private app this is useful. In production it can expose internals, stack
traces, worksheet names, or credential parsing details.

Recommendation:

- Show friendly error text to users.
- Log exception details to an operator channel or monitoring tool.
- Gate stack traces behind a debug flag.

## P3 Performance Findings

### P3-13: CSS is read from disk on every rerun

Evidence:

- `gym_pledge/dashboard.py:32` reads CSS text each run.

Impact:

Small cost, but avoidable.

Recommendation:

- Wrap CSS loading in `@st.cache_data`.

### P3-14: Google client setup is not resource-cached

Evidence:

- `gym_pledge/data/source.py:25` builds credentials and authorizes gspread
  inside `read_google_sheet_as_df()`.

Impact:

`st.cache_data` caches function outputs, but the client itself is not a
resource. This matters when cache misses happen.

Recommendation:

- Add a private `@st.cache_resource` helper for the authorized gspread client.

### P3-15: Reads use `get_all_values()`

Evidence:

- `gym_pledge/data/source.py:30`.

Impact:

The app reads entire worksheets, including unused columns/rows.

Recommendation:

- Restrict read ranges if the sheets grow.
- Or use `get_all_records()` with expected headers and explicit validation.

### P3-16: Matplotlib figures are not closed

Evidence:

- `st.pyplot()` calls in About, Scorecard, Personalization, and Common helpers
  do not consistently close figures.

Impact:

Repeated Streamlit reruns can accumulate figure objects.

Recommendation:

- After each `st.pyplot(fig)`, call `plt.close(fig)`.
- Or use Altair consistently for web charts.

### P3-17: All page modules are imported at app startup

Evidence:

- `dashboard.py:9` to `dashboard.py:15` imports every page.

Impact:

Heavy chart libraries and hidden pages load even if a user only wants the
form or About page.

Recommendation:

- Lazy-import page modules inside route branches.
- Especially avoid importing Matplotlib-heavy pages for static pages.

### P3-18: Cumulative race can create large dense grids

Evidence:

- `gym_pledge/ui/common.py:2633` builds name x day grid.

Impact:

Fine for a small group, but the algorithm scales linearly with participants
and days on every rerun.

Recommendation:

- Cache `build_cumulative_calories_long()` by input hash/month.
- Keep as-is if group size is permanently small, but document that assumption.

## P4 Low-Level Code Quality Findings

### P4-01: Public functions lack consistent type hints

Evidence:

- `dashboard.load_css()` has no return type.
- Many UI helpers accept untyped `df`/`lb`.
- `month_leaderboard()` has untyped `all_users`.

Impact:

This blocks useful static analysis and makes agent edits riskier.

Recommendation:

- Add type hints to public helpers and data-layer functions.
- Start with functions called across modules.

### P4-02: `except Exception: pass` patterns hide causes

Evidence:

- `app_time.py:20`
- `app_time.py:45`
- `yearcalendar.py:27`

Impact:

Fallbacks are sometimes okay, but silent broad catches make debugging
configuration errors harder.

Recommendation:

- Catch specific exceptions where possible.
- For timezone fallback, warn once or document that invalid timezones fall
  back to local system time.

### P4-03: Month selection behavior is unintuitive

Evidence:

- `dashboard.py:122` hides month selector on Leaderboard, About, Trends, and
  Yearbook.
- Yearbook derives year from hidden `month_selected`.

Impact:

Users cannot intentionally select a Yearbook year from the Yearbook page. It
uses the default selected month behind the scenes.

Recommendation:

- Give Yearbook a visible year selector.
- Give Scorecard a clear month selector.
- Make Leaderboard's "current month only" behavior explicit.

### P4-04: Copy and function names mix "Users" and "Participants"

Evidence:

- Config says `USERS_*`.
- UI mostly says participant.
- Data source function is `get_users()`.

Impact:

Minor, but inconsistent domain language accumulates.

Recommendation:

- Rename external-facing domain concept to "participants".
- Keep backward-compatible alias if necessary.

### P4-05: Inline HTML styles are everywhere

Evidence:

- About, Scorecard, Yearbook, Common, and Dashboard all inject inline style
  blocks.

Impact:

Visual behavior is hard to reason about and hard to test.

Recommendation:

- Move reusable styles to `theme.css` with explicit class names.
- Keep dynamic inline style only for truly data-driven values.

## Production-Ready Alternatives

These are not necessarily all required for a friend-group app. They are what
"production level" would look like.

1. Typed settings layer:
   - Validate spreadsheet ID, worksheet names, timezone, form URL, Venmo URL,
     cutoff defaults, and per-month overrides at startup.
   - Fail fast with actionable messages.

2. Data contract validation:
   - Use a small schema layer for cleaned DataFrames.
   - Validate columns, dtypes, required non-null fields, and value ranges.

3. Data-quality report:
   - Every refresh should know how many rows were read, dropped, repaired, and
     retained.
   - Show this in an admin/debug expander.

4. Safer rendering layer:
   - Native Streamlit tables by default.
   - Centralized escaped HTML helper for rare custom markup.

5. Streamlit smoke tests:
   - Mock Google Sheets.
   - Load each page.
   - Assert no exception banner.

6. Visual regression:
   - Playwright screenshots for desktop and mobile.
   - Pixel checks for nonblank charts.

7. Auth/privacy gate:
   - Shared password or OAuth allowlist.
   - Do not rely on obscurity for participant history.

8. Observability:
   - Capture runtime exceptions.
   - Track refresh failures and sheet read failures.

9. Dependency/security checks:
   - Add `uv audit` or `pip-audit`.
   - Keep Dependabot but do not rely on it alone.

10. Chart system consolidation:
   - Prefer Altair for web-native charts.
   - Remove Apex CDN unless there is a strong reason.
   - Reduce Matplotlib usage or close figures rigorously.

11. Package/import sanity:
   - Either make the flat layout a documented design or package the app
     conventionally.

12. Release/deploy confidence:
   - Post-deploy health check.
   - Rollback instructions are in docs, but the app should also tolerate data
     source outages gracefully.

## Suggested Remediation Roadmap

### Phase 1: Stop shipping misleading data

1. Resolve same-day workout aggregation vs dedupe.
2. Add data-quality report from `clean()`.
3. Fix missing roster month fallback.
4. Normalize roster and form names through one helper.
5. Fix About/Scorecard hard-coded rule copy.

### Phase 2: Make unsafe rendering boring

1. Escape every dynamic value used in raw HTML/SVG.
2. Replace custom HTML tables with native dataframes where possible.
3. Add hostile-input tests for participant names.
4. Remove broad keyed-container CSS.

### Phase 3: Prove the app works, not just helper functions

1. Add Streamlit page smoke tests with mocked data.
2. Add mobile and desktop screenshot smoke tests.
3. Add source-boundary tests for `get_users()` and `get_data()`.
4. Add dashboard routing tests.

### Phase 4: Clean up design and maintainability

1. Split `ui/common.py`.
2. Centralize theme tokens.
3. Remove deprecated helpers.
4. Expose or delete hidden pages.
5. Tighten copy and reduce instructional captions.

### Phase 5: Production posture

1. Add type checking.
2. Add dependency audit.
3. Add auth/privacy gate.
4. Add runtime error monitoring.
5. Add post-deploy health check.

## Highest-Impact Quick Wins

If the next agent wants visible progress fast:

1. Change the Scorecard winner copy to remove the false 4000+ calorie claim.
2. Show About and Log pages without loading Google Sheets.
3. Add a warning when the active-user month column is missing.
4. Escape dynamic names in podium, lazy bubbles, and styled tables.
5. Replace the fixed Google Form iframe with responsive embed plus link.
6. Remove the global `div[class^="st-key-"]` card styling.
7. Add `get_users()` tests.
8. Add a data-quality drop-count report from `clean()`.
9. Update README setup commands to use `uv` and canonical `python -m pytest`.
10. Add a visible Yearbook year selector.

## Final Adversarial Note

This repo has the bones of a disciplined small app: docs, ADRs, tests, CI,
and a clear domain. The next level is not more decorative CSS or another chart.
The next level is making the app unable to lie.

The app should never silently count the wrong people, silently drop important
rows, silently render unsafe sheet values, or pass tests that do not exercise
the shipped user path. Fix those, and the rest of the polish work will matter.
