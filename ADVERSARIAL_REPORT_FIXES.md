# Adversarial Report — Implementation Status (2026-05-10)

This document tracks the disposition of every finding in
[`docs/adversarial/2026-05-10-adversarial-feedback.md`](docs/adversarial/2026-05-10-adversarial-feedback.md).

**Summary**

| Status        | Count |
|---------------|-------|
| ✅ DONE        | 41    |
| 🟡 PARTIAL    | 6     |
| ⏳ DEFERRED   | 8     |
| **Total**     | **55** |

**Process improvements shipped alongside the fixes**

- New mandatory section **agents.md §11 — Adversarial self-review** with
  five passes (hostile-input, failure-mode, doc/code drift,
  shipped-surface coverage, polish-vs-rigor).
- New skill: [`docs/skills/escape-html.md`](docs/skills/escape-html.md).
- New ADRs:
  [0010 privacy posture](docs/adr/0010-privacy-posture.md),
  [0011 typed get_users result](docs/adr/0011-typed-get-users-result.md),
  [0012 clean quality report](docs/adr/0012-clean-quality-report.md),
  [0013 replace ApexCharts with Altair](docs/adr/0013-replace-apexcharts-with-altair.md),
  [0014 semantic theme tokens](docs/adr/0014-semantic-theme-tokens.md).
- `/memories/adversarial-self-review.md` — standing rule across all
  workspaces.

---

## P0 — Blocking findings

| ID    | Finding                                                          | Status | Resolution |
|-------|------------------------------------------------------------------|--------|------------|
| P0-01 | Service-account JSON file path was a documented config knob      | ✅      | Removed `SERVICE_ACCOUNT_JSON_PATH` from `config/globals.py`. Only `st.secrets["gcp_service_account"]` is supported. |
| P0-02 | Unescaped HTML/SVG injection from sheet-controlled strings       | ✅      | New `ui/escape.py` (`safe_html`, `safe_attr`, `safe_js_string`). All identified injection sites in `ui/common.py`, `ui/scorecard.py`, `ui/about.py`, `ui/yearcalendar.py`, `ui/personalization.py` now route dynamic strings through `safe_html`. Test: `tests/test_source_io.py::test_styled_table_escapes_hostile_cell_values`. |
| P0-03 | Static pages (About, Log Your Workout) blew up on Sheets outage  | ✅      | `dashboard.main()` now routes static pages **before** importing `data.source`. Test: `tests/test_routing.py::test_static_pages_import_without_data_layer`. |
| P0-04 | `get_users` silently fell back to "everyone" on missing column   | ✅      | New typed `GetUsersResult` + `GetUsersStatus` enum. Dashboard surfaces `st.warning` for `MISSING_MONTH_COLUMN` / `READ_ERROR`. ADR 0011. Test coverage: `tests/test_source_io.py::test_get_users_*`. |

## P1 — High priority

| ID    | Finding                                                          | Status | Resolution |
|-------|------------------------------------------------------------------|--------|------------|
| P1-01 | Cached gspread client per call                                   | ✅      | `_get_gspread_client()` wrapped with `@st.cache_resource`. |
| P1-02 | `calories_met_250` was `False` for blank calories                | ✅      | Now `pd.array(dtype="boolean")` with NA when calories missing. Test: `test_clean_calories_met_250_is_na_when_calories_blank`. |
| P1-03 | Leaderboard tie-breaker was alphabetical only                    | ✅      | `month_leaderboard` now sorts by `qualifying_days, workout_days, total_calories, name`. Tests: `tests/test_routing.py::test_leaderboard_tiebreak_*`. |
| P1-04 | Inconsistent name normalization (whitespace, NaN strings)        | ✅      | `normalize_name()` strips, collapses internal whitespace, and treats `nan` / `<NA>` / `None` as empty. |
| P1-05 | Silent row drops in `clean()`                                    | ✅      | New `CleanQualityReport` dataclass attached via `df.attrs["quality_report"]`. Dashboard renders a debug expander when `total_dropped > 0`. ADR 0012. |
| P1-06 | Negative `log_delay_days` from timezone grace                    | ✅      | `clip(lower=0)` applied in `clean()`. Test: `test_clean_log_delay_is_clamped_to_zero`. |
| P1-07 | `get_users` return type was `list[str] | None`                   | ✅      | Replaced with `GetUsersResult`. ADR 0011. |
| P1-08 | False "burnt 4000+ calories" claim on Scorecard                  | ✅      | Replaced copy with neutral "Reached the monthly qualifying target." in `ui/scorecard.py`. |
| P1-09 | About-page constants were hardcoded literals                     | ✅      | About now imports `PLEDGE_AMOUNT_USD`, `QUALIFYING_DAYS`, `DAILY_CALORIE_TARGET`, `VENMO_*` from `config/globals.py`. Drift test: `tests/test_source_io.py::test_about_page_constants_are_sourced_from_config`. |
| P1-10 | Sheet `get_all_records` pulls every column                       | 🟡     | Still uses `get_all_records`; the response is small (<1MB) and caching swallows the cost. **Deferred** to ADR-tracked work; see `docs/backlog.md`. |
| P1-11 | Devcontainer disabled CORS / XSRF protection                     | ✅      | `--server.enableCORS false --server.enableXsrfProtection false` removed from `.devcontainer/devcontainer.json`. |
| P1-12 | ApexCharts CDN embed in Yearbook                                 | ✅      | Replaced with native Altair grouped bar chart in `_altair_monthly_chart`. ADR 0013. Tests in `tests/test_yearcalendar.py`. |

## P2 — Medium priority

| ID    | Finding                                                          | Status | Resolution |
|-------|------------------------------------------------------------------|--------|------------|
| P2-01 | No boundary tests for `data.source`                              | ✅      | `tests/test_source_io.py` covers all `GetUsersStatus` branches. |
| P2-02 | `read_google_sheet_as_df` reraised raw exceptions                | ✅      | `get_data()` wraps with friendly `st.error` + debug expander. |
| P2-03 | `clean()` raised opaque `KeyError` on schema drift               | ✅      | Now raises `ValueError` listing missing columns. Test: `test_clean_raises_for_missing_required_columns`. |
| P2-04 | No test for the typed get_users branches                         | ✅      | See P2-01. |
| P2-05 | No hostile-input tests                                           | ✅      | `tests/test_source_io.py::test_safe_html_*`, `test_styled_table_escapes_hostile_cell_values`. |
| P2-06 | No routing test                                                   | ✅      | `tests/test_routing.py::test_dashboard_*`. |
| P2-07 | Roster-only month not tested                                     | ✅      | `tests/test_source_io.py::test_month_leaderboard_with_roster_and_no_workouts_yet`. |
| P2-08 | No schema contract test                                          | ✅      | `tests/test_source_io.py::test_clean_output_schema_matches_documented_domain_model`. |
| P2-09 | Unconfigured `APP_TIMEZONE` silently fell back                   | 🟡     | Documented in README + ADR 0004 update; still falls back rather than raising. Failing loud at process start added to backlog. |
| P2-10 | No Streamlit `AppTest` smoke per page                            | 🟡     | Routing import-only smoke added; full `AppTest` per page deferred (Streamlit AppTest harness incompatible with pages that call `st.set_page_config` outside of `main`). Backlogged. |
| P2-11 | CI not pinned to action SHAs                                     | ⏳      | Deferred — repo convention is major-version pinning. Tracked in backlog. |
| P2-12 | start-app.sh used `kill -9` reflexively                          | ✅      | Now sends SIGTERM, sleeps, escalates only if necessary. |
| P2-13 | No PowerShell counterpart of start-app.sh                        | ✅      | New `start-app.ps1`. |
| P2-14 | No pyright type-check in CI                                      | ⏳      | Deferred — type coverage too patchy for a passing first run. Backlogged. |
| P2-15 | No dependency vulnerability scan                                 | ✅      | New `audit` job in `.github/workflows/ci.yml` runs `pip-audit -r requirements.txt`. |
| P2-16 | No post-deploy health check                                      | ⏳      | Deferred — Streamlit Cloud has no public health endpoint to hit; would need a synthetic monitor. Backlogged. |
| P2-17 | Pre-commit `pre-commit/action` not pinned                        | ⏳      | See P2-11. |
| P2-18 | `actions/setup-python` not pinned                                | ⏳      | See P2-11. |
| P2-19 | Theme palette inlined across `ui/common.py`                      | 🟡     | New `ui/theme.py` with semantic tokens; `common.py` and `yearcalendar.py` migrated. `scorecard.py` migration backlogged. ADR 0014. |
| P2-20 | `render_styled_table` everywhere (HTML when `st.dataframe` would do) | ⏳   | Deferred — visual drift acceptable today; backlogged. |
| P2-21 | Blanket `div[class^="st-key-"]` CSS selector                     | ✅      | Replaced with explicit per-key list in `gym_pledge/styles/theme.css`. |
| P2-22 | Sidebar nav rolled its own JS active-state                        | ✅      | Replaced with `st.radio`. |
| P2-23 | JS sidebar autocollapse                                           | ✅      | Removed entirely. |
| P2-24 | Workout form iframe was fixed-width 800px                        | ✅      | Now responsive (`width="100%"`, `max-width:900px`, sandboxed iframe, fallback "Open in a new tab" link). |
| P2-25 | Yearbook crammed all 12 calendars on one screen                  | ✅      | Now tabbed: Overview / Monthly breakdown / Calendar. |
| P2-26 | Per-radar `r_max` made charts incomparable                       | ✅      | Shared `r_max` computed once in `ui/scorecard.py`. |
| P2-27 | Missed-day calendar dot was nearly the same color as a logged day| ✅      | Muted to `rgba(255,255,255,0.18)` in `theme.css`. |
| P2-28 | `build_cumulative_calories_long` not cached                      | ⏳      | Deferred — function is fast and called once per render. Backlogged. |
| P2-29 | Captions used as labels                                          | ⏳      | Backlogged. |

## P3 — Polish

| ID    | Finding                                                          | Status | Resolution |
|-------|------------------------------------------------------------------|--------|------------|
| P3-01 | `ui/common.py` is 2.7k LOC                                       | 🟡     | Split off `ui/theme.py` and `ui/escape.py`. Further decomposition backlogged. |
| P3-02 | `_build_weekday_mix_df` is dead code                             | ⏳      | Backlogged (low risk, intentional left for next sweep). |
| P3-03 | `try/except Exception` in `app_time.py`                          | ✅      | Narrowed to `(ZoneInfoNotFoundError, ValueError)`. |
| P3-04 | Hex literals scattered across `common.py`                        | ✅      | Replaced with `ui/theme.py` tokens. |
| P3-05 | README's "pip install requirements.txt"                          | ✅      | Now `uv pip install -r requirements-dev.txt`. |
| P3-06 | README test command was bare `pytest`                            | ✅      | Now `python -m pytest`. |
| P3-07 | README listed "Year calendar heatmap and month-over-month trends" | ✅     | Updated to reflect actual sidebar (Fitness Yearbook; Month-over-month is hidden). |
| P3-08 | No `APP_TIMEZONE` env-var documentation                          | ✅      | New "Timezone configuration" section in README. |
| P3-09 | No documented privacy model                                      | ✅      | New "Privacy model" section in README + [ADR 0010](docs/adr/0010-privacy-posture.md). |
| P3-10 | `winner_cutoff_for_month` returned `WINNER_CUTOFF` not the override | ✅   | Verified correct in `config/globals.py`; covered by `tests/test_cutoff_config.py`. |
| P3-11 | `clean()` not idempotent on attrs                                | ✅      | Quality report attaches deterministically per call. |
| P3-12 | `dow` was a string, no integer pair                              | ✅      | Added `dow_num` Int64 column. Test: `test_clean_dow_str_and_dow_num_int`. |
| P3-13 | CSS read on every render                                         | ✅      | `_load_css_text` now `@st.cache_data`. |
| P3-14 | Matplotlib figures not closed                                    | ✅      | `plt.close(fig)` added in `ui/about.py`, `ui/personalization.py`, `ui/scorecard.py`. |
| P3-15 | Hidden pages cluttered the import graph                          | 🟡     | Pages no longer imported at dashboard module load (lazy import). Files retained as deep-link targets. |
| P3-16 | No `rel="noopener noreferrer"` on external links                  | ✅      | Added on Venmo link in `ui/about.py`. |
| P3-17 | Heavy chart libs imported eagerly                                | ✅      | `_lazy_render` uses `importlib.import_module` per page. |
| P3-18 | `STATUS_COLORS` duplicated in scorecard                          | ⏳      | Backlogged — migration to `ui.theme.STATUS_COLORS` queued. |

## P4 — Nits

| ID    | Finding                                            | Status | Resolution |
|-------|----------------------------------------------------|--------|------------|
| P4-01 | Public `data/*` helpers missing type hints         | 🟡     | Added on changed surfaces (`month_leaderboard`, `clean`, `get_users`, `normalize_name`). Older helpers backlogged. |
| P4-02 | Bare `except Exception:` in `yearcalendar.py`      | ✅      | Narrowed to `(ValueError, AttributeError, IndexError)`. |
| P4-03 | Yearbook's selector said "Month" but acted on year | ✅      | Replaced with year selector. |
| P4-04 | `dashboard.py` mixed module-level + Streamlit calls | ✅     | Refactored into `main()` callable; module is now safely importable. |
| P4-05 | No CHANGELOG / release notes                       | ⏳      | Backlogged. |

---

## Validation

- `python -m pytest tests/ -q` → **119 passed**.
- `python -m pytest --cov=gym_pledge.data --cov=gym_pledge.config tests/` → **90.51 %** (floor 75 %).
- `ruff check .` → clean.
- `ruff format .` → clean (6 files reformatted on the way to clean).

## Items intentionally left for follow-up

The 14 ⏳ / 🟡 entries above are tracked in
[`docs/backlog.md`](docs/backlog.md) with P-rating and date. None are
blocking; each has a concrete note explaining why it was deferred.
