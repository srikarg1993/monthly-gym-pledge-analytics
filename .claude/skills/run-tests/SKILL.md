---
name: run-tests
description: Run the pytest suite for the gym-pledge analytics repo. Use when the user asks to "run tests", "check if tests pass", or after making changes to data/metrics/config code.
---

# Run the test suite

Tests live under `tests/` and cover data cleaning, leaderboard metrics, cutoff config, and the year calendar page.

## Run everything

```bash
pytest tests/
```

The test files manually prepend `gym_pledge/` to `sys.path`, so no editable install is needed.

## Run a single file / test

```bash
pytest tests/test_metrics.py
pytest tests/test_metrics.py::test_month_leaderboard_basic -v
```

## After which kinds of changes

Always run the relevant subset before reporting work done:

| Changed file                           | Run at minimum                              |
|----------------------------------------|---------------------------------------------|
| `gym_pledge/data/source.py`            | `tests/test_source.py`                      |
| `gym_pledge/data/metrics.py`           | `tests/test_metrics.py`                     |
| `gym_pledge/config/globals.py`         | `tests/test_cutoff_config.py`               |
| `gym_pledge/ui/yearcalendar.py`        | `tests/test_yearcalendar.py`                |
| Anything crossing multiple modules     | full `pytest tests/`                        |

## When a test fails

- Do **not** add an `xfail` / skip to make red go green — diagnose and fix the underlying cause or revert the offending change.
- If the test itself is stale (e.g., a cutoff date passed), update the fixture, not the assertion logic.

## Gaps to be aware of

UI pages under `gym_pledge/ui/` other than `yearcalendar` have no direct coverage — exercise those manually via the `run-app` skill when changing them. The Q/W% divide-by-zero fix in `scorecard.py` is also not unit-tested; smoke-test the Scorecard page manually when a month has any participant with zero workout days.
