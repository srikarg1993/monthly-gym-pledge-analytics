# ADR 0004: Centralize "now" via `app_time.py` and `APP_TIMEZONE`

- **Status**: Accepted
- **Date**: 2026-05-05
- **Tags**: time, testability

## Context

The dashboard makes many "current month / today" decisions: which month to
default to in the leaderboard, which days to highlight on the calendar, which
participants count as "still active" for the cutoff race. Calling
`datetime.now()` / `date.today()` directly in each module had two failures:

1. **Timezone drift**: when the Streamlit host is in UTC but the group lives
   in US Central, "today" flips at the wrong moment.
2. **Untestable**: tests can't easily pin "now" to a known instant when each
   module reaches into the stdlib directly.

## Decision

Introduce `gym_pledge/app_time.py` with `now_app()`, `today_app()`, and
`current_month_str()`. They read the `APP_TIMEZONE` environment variable
(default `America/Chicago`) and produce timezone-aware values via `zoneinfo`.

All app code calls these helpers. Tests freeze time by passing dates directly
into the pure functions in `data/metrics.py` rather than invoking `today_app()`.

## Consequences

### Positive
- One place to change the group's effective timezone.
- Pure metrics functions stay testable — they take dates as arguments, not
  side effects.
- The Streamlit dev container and CI both honor `APP_TIMEZONE` automatically.

### Negative
- Anyone adding new date logic must remember to import from `app_time`. This
  is enforced by `agents.md` and convention, not by tooling.

## Alternatives considered

- **`pytz`**: rejected — `zoneinfo` is in the stdlib for Python 3.9+.
- **Pin a literal timezone string in code**: rejected — operational
  inflexibility.
