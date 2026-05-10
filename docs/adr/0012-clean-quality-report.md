# 0012 — `CleanQualityReport` attached to cleaned DataFrame

**Status**: Accepted
**Date**: 2026-05-10
**Driver**: 2026-05-10 adversarial review (P1-05)

## Context

`data.source.clean(raw)` quietly dropped rows for six different reasons
(blank name, NaT timestamp, too-old workout date, future workout date,
unparseable calories, calories out of range). The user had no way to
see which rows had been dropped or why; a typo in the form could halve
the visible standings without leaving a trace.

## Decision

`clean()` now builds a `CleanQualityReport` (frozen dataclass) and
attaches it to `df.attrs["quality_report"]`:

```python
@dataclass(frozen=True)
class CleanQualityReport:
    rows_in: int = 0
    rows_out: int = 0
    dropped_blank_name: int = 0
    dropped_nat_timestamp: int = 0
    dropped_too_old: int = 0
    dropped_future: int = 0
    dropped_bad_calories: int = 0
    dropped_calories_out_of_range: int = 0

    @property
    def total_dropped(self) -> int: ...
    def as_dict(self) -> dict[str, int]: ...
```

`dashboard.main()` reads the report and, when `total_dropped > 0`,
shows it inside a collapsed `st.expander("Data quality")`. Diagnostics
without spam.

## Consequences

### Positive
- Drops are now observable. Future bugs in form parsing don't hide.
- The report is a pure side-channel — adding a new drop reason is a
  one-line counter increment and a one-line dataclass field.

### Negative
- `df.attrs` does not survive every pandas operation (e.g. concat).
  Callers downstream of `clean()` must avoid wiping attrs if they want
  the report to flow through. Today only `dashboard.main()` reads it,
  so the constraint is contained.

### Neutral
- Tests (`tests/test_source_io.py::test_clean_quality_report_*`) lock
  in the counter behaviour for each drop reason.
