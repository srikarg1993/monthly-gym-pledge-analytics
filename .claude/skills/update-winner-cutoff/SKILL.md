---
name: update-winner-cutoff
description: Change the monthly workout-count threshold required to "win" the pledge — globally or for a specific month. Use when the user asks to "change the cutoff", "lower/raise the target", "override February to 15", etc.
---

# Update the winner cutoff

The cutoff is the number of qualifying workout days (`burnt_250 = True`) a participant needs in a month to be marked `is_winner = True`.

## Where cutoffs live

`gym_pledge/config/globals.py`:

- `WINNER_CUTOFF` — integer, the default for every month.
- `WINNER_CUTOFF_BY_MONTH` — `dict[str, int]` keyed by `"YYYY-MM"`, overrides the default for specific months.
- `winner_cutoff_for_month(month_str)` — resolver used throughout the app. Always read through this function, never hardcode.

## How to change

**Global change (affects all months without an override):**
Edit `WINNER_CUTOFF` in `gym_pledge/config/globals.py`.

**One-off month override (recommended for short months or special events):**
Add an entry to `WINNER_CUTOFF_BY_MONTH`:

```python
WINNER_CUTOFF_BY_MONTH = {
    "2026-02": 15,   # short month
    "2026-12": 12,   # holidays
}
```

Keys are `YYYY-MM` strings matching the `month` column produced by `data.source.clean()`.

## After any change

1. Update / add an assertion in `tests/test_cutoff_config.py` so the override is locked in.
2. Run `pytest tests/test_cutoff_config.py tests/test_metrics.py`.
3. Spot-check the leaderboard page for the affected month via the `run-app` skill — `workouts_left` and `is_winner` should reflect the new cutoff.

## Do NOT

- Hardcode the cutoff inline in `metrics.py` or any UI file. Call `winner_cutoff_for_month()`.
- Retroactively change a cutoff for a month that has already concluded — past winners were declared under the prior value.
