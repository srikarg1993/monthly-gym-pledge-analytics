# Skill: Writing tests, fixtures, and coverage expectations

Trigger: any change to `data/*` or `config/*`; any new `_build_*` helper
in a UI module.

## How tests are structured

- `tests/` sits at repo root.
- Each test file mirrors a module: `test_source.py` ↔ `data/source.py`.
- Tests insert `gym_pledge/` onto `sys.path` themselves (see top of any
  existing test file). No `pip install -e .` needed.
- Run with: `python -m pytest tests/ -q`.
- `pyproject.toml` enables `--strict-markers` and `--strict-config` so a
  typo in a `@pytest.mark.foo` decorator or in `[tool.pytest.ini_options]`
  fails fast instead of silently no-op'ing. If you add a new marker,
  declare it under `[tool.pytest.ini_options] markers = [...]`.

## Coverage floor

- **75 %** on `gym_pledge/data/*` and `gym_pledge/config/*`. Measured with
  **branch coverage** enabled (see `[tool.coverage.run] branch = true` in
  `pyproject.toml`). The terminal report has a `BrPart` column showing
  partial-branch misses. Investigate any non-zero `BrPart` count before
  shipping.
- Run with: `python -m pytest` (the `addopts` in `pyproject.toml` already
  pass `--cov=data --cov=config --cov-branch --cov-fail-under=75`).
- UI render functions are not held to this floor (their `_build_*` helpers
  are).
- Chart specs in `ui/common.py` are not snapshot-tested.

## What every new `data/*` function needs

1. **Happy path**: realistic DataFrame with 2-4 names, multiple dates,
   mixed `burnt_250` flags.
2. **Empty input**: pass `pd.DataFrame()` and assert no exception, expected
   empty result.
3. **Edge case relevant to the metric**: single-user month, all-winner month,
   no-qualifying month, etc.

## Fixtures

Inline `pd.DataFrame(...)` literals at the top of each test. We deliberately
**do not** maintain a fixtures module — keeping fixtures inline keeps the
test self-explanatory.

The minimum fixture for a workout DataFrame:

```python
import pandas as pd
from datetime import date

df = pd.DataFrame([
    {"name": "Alice", "workout_date": date(2026, 5, 1), "burnt_250": True,
     "month": "2026-05", "calories_burned": 300, "log_delay_days": 0.0,
     "timestamp": pd.Timestamp("2026-05-01 18:00")},
    # ...
])
```

Match the **Domain model** table in [`agents.md`](../../agents.md#L130).

## What never goes in tests

- Live Google Sheets API calls.
- Real `st.secrets` reads.
- `datetime.now()` / `date.today()` — pin dates as literals.
- Network calls of any kind.

## Cutoff overrides

Any change to `WINNER_CUTOFF_BY_MONTH` or `winner_cutoff_for_month` requires
adding or updating a test in `tests/test_cutoff_config.py`.
