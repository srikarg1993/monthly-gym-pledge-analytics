# 0011 — Typed `GetUsersResult` for the active-user roster

**Status**: Accepted
**Date**: 2026-05-10
**Driver**: 2026-05-10 adversarial review (P0-04, P1-07)

## Context

`data.source.get_users(month)` previously returned `list[str] | None`.
Three failure modes (Sheets API error, missing month column, no active
users) all collapsed to either `None` or `[]`, and the dashboard used a
truthiness check (`users or None`) to decide whether to fall back to
"everyone in the workout DataFrame".

The 2026-05-10 adversarial review caught a P0 consequence: when the
month column was missing (e.g. someone forgot to add the new month's
column to the Venmo Tracker sheet), the function returned `[]`, the
dashboard fell back to "everyone", and the leaderboard silently lied
about who was "In" for the month.

## Decision

`get_users` now returns a `GetUsersResult` dataclass:

```python
@dataclass(frozen=True)
class GetUsersResult:
    users: list[str]
    status: GetUsersStatus
    message: str = ""

    @property
    def ok(self) -> bool: ...
```

with an `Enum` for the failure modes:

```python
class GetUsersStatus(Enum):
    OK
    READ_ERROR
    EMPTY_SHEET
    MISSING_NAME_COLUMN
    MISSING_MONTH_COLUMN
    NO_ACTIVE_USERS
```

The dashboard now branches explicitly on `MISSING_MONTH_COLUMN` /
`READ_ERROR` and surfaces a `st.warning` so the user knows the
leaderboard is roster-blind. Back-compat is preserved via
`__bool__` / `__iter__` / `__len__` on `GetUsersResult`, so existing
callsites that wrote `if users:` or `for u in users:` keep working
without change.

## Consequences

### Positive
- Failure modes are visible to the caller and to the user.
- The "missing column" foot-gun cannot recur silently — it now surfaces
  as a yellow warning bar.
- Tests (`tests/test_source_io.py`) assert each branch.

### Negative
- The dataclass adds a tiny indirection at every callsite.

### Neutral
- The change is fully backward-compatible for code that just iterated
  over the return value.
