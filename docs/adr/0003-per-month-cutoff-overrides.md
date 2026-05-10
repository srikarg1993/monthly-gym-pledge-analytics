# ADR 0003: Per-month winner-cutoff overrides via config dict

- **Status**: Accepted
- **Date**: 2026-05-05
- **Tags**: config, domain

## Context

The pledge requires a fixed number of qualifying workouts per month to "win"
(default 16). Some months are short (February) or have known group conflicts
(holidays, travel weeks), and the group occasionally votes to lower the bar
for that month only.

Previously, lowering the bar required editing `WINNER_CUTOFF` directly, which
either retroactively lowered prior months or required ad-hoc branching in
metrics code.

## Decision

Introduce `WINNER_CUTOFF_BY_MONTH: dict[str, int]` in
`gym_pledge/config/globals.py`, keyed by `YYYY-MM`. All UI and metrics code
resolves the cutoff via `winner_cutoff_for_month(month_str)`, which returns
the override if present and `WINNER_CUTOFF` otherwise.

`winner_cutoff_for_month` clamps to `max(int(value), 1)` and falls back to
the default on any `TypeError` / `ValueError`, so misconfigured entries can't
silently produce negative or zero cutoffs.

## Consequences

### Positive
- Past months are immutable; only the listed month is affected.
- Single source of truth — no inline cutoffs in metrics or UI.
- Test coverage in `tests/test_cutoff_config.py` exercises both default and
  override resolution.

### Negative
- The dict can drift if someone forgets to remove a stale override after the
  month ends. Acceptable cost — the override only matters when that exact
  month is queried.

## Alternatives considered

- **Per-row override in the sheet**: rejected — distant from code review,
  risk of accidental edits.
- **Environment variable per month**: rejected — operational overhead and
  fragility on deploy.
