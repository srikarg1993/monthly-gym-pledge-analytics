# ADR 0007: Audit pass — remove dead chart helpers and tighten type hints

- **Status**: Accepted
- **Date**: 2026-05-05
- **Tags**: cleanup, types

## Context

A multi-pass audit was performed on the entire repository (see commit log
around the same date). The audit confirmed the codebase is in good shape —
no security issues, no hardcoded credentials, no duplicated logic, all
data-layer functions are idempotent. The audit surfaced a small number of
concrete, low-risk hygiene items:

1. Two chart helpers in `gym_pledge/ui/common.py` were defined but never
   imported anywhere in the live app:
   - `alt_weekday_bubble` (Altair bubble chart, superseded by
     `weekday_radar_figure`)
   - `render_donut_days_left` (matplotlib donut, superseded by the
     `alt_goal_ladder_chart` summary chip)
2. Several functions in `data/metrics.py` and `data/source.py` were missing
   type hints on signatures: `longest_streak`, `fastest_winner_date`,
   `lazy_logger_score`, `frontload_vs_cram`, `month_bounds`, `normalize_bool`.
3. A mojibake string in `ZONE_ORDER` (`"Â½â€"1 day"`) was a UTF-8 corruption
   of the intended `"½–1 day"` from a prior copy-paste round-trip.
4. Edge-case branches in `longest_streak` (duplicates, `None` values,
   single-date input), `month_bounds` (leap-year February, 30-day months),
   `winner_cutoff_for_month` (malformed override values), and
   `normalize_bool` (full truthy / falsy matrix) were not directly covered
   by tests.

## Decision

In a single pass:

- Delete `alt_weekday_bubble` and `render_donut_days_left` from
  `ui/common.py`. They had zero callers across the live tree (verified via
  workspace-wide grep).
- Add type hints to the affected `data/*` functions.
- Fix the `ZONE_ORDER` string to the correct Unicode characters.
- Add `tests/test_audit_edge_cases.py` covering the gaps listed above. The
  new tests use only the existing inline-DataFrame fixture pattern; no new
  fixture files.

No public function signatures changed in a breaking way (added optional
type hints only). No data shapes changed.

## Consequences

### Positive
- ~115 lines of dead code removed from `common.py`.
- Type hints make `pyright` / IDE hover info more useful.
- Coverage on `data/metrics.py` and `data/source.py` improved without
  inflating the test suite with redundant cases.

### Negative
- None identified. The dead helpers are recoverable from git history if
  ever needed; the audit confirmed no callers.

### Neutral
- The audit also reviewed `gym_pledge/00_Archive/` — no changes there per
  [ADR 0006](0006-archive-folder-policy.md).

## Alternatives considered

- **Keep dead code "just in case"**: rejected — it confuses static analysis
  and skews the audit signal-to-noise ratio. Git history retains anything
  important.
- **Convert dead helpers into a `legacy/` namespace**: rejected — the
  archive folder already serves that role.

## References

- Audit report (in conversation transcript, 2026-05-05).
- New test file: `tests/test_audit_edge_cases.py`.
