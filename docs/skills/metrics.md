# Skill: Adding a new analytical function

Trigger: a UI page needs a new derived metric (per-person stat, group
aggregate, etc.).

## Where it goes

`gym_pledge/data/metrics.py`. UI code never inlines pandas aggregations
beyond trivial `.groupby` for layout.

## The recipe

1. **Sketch the signature**:
   ```python
   def my_metric(df: pd.DataFrame, *, month_str: str, cutoff: int) -> pd.DataFrame:
       ...
   ```
   - First positional arg is always the workout DataFrame.
   - All other args keyword-only.
   - Type hints required on signature.
2. **Pure function**: same input → same output, no side effects, no
   `st.cache_data`, no `datetime.now()`. If you need "today", accept it as a
   parameter so tests can pin it.
3. **Copy before mutating**: `d = df.copy()` at the top.
4. **Empty-input guard**: return an empty DataFrame with the expected schema,
   not `None`, when input is empty — unless the caller specifically expects
   `None` (see `lazy_logger_score` precedent).
5. **Consistent column names**: use `name`, `workout_date`, `qualifying_days`,
   etc., matching the rest of the module.
6. **Idempotent**: re-running on the same input must produce identical output
   (same row order, same dtypes). Sort explicitly before returning.
7. **Resolve cutoffs via `winner_cutoff_for_month`** — never hardcode.

## Tests

In `tests/test_metrics.py`, add at minimum:

- A happy-path test with 2-3 names spanning multiple dates.
- An empty-DataFrame test.
- An edge case relevant to your metric (single user, all-winner month, etc.).

Use the existing fixtures (synthetic DataFrames built inline) — don't
introduce new fixture files.

## Reference implementations

- Per-person leaderboard: `month_leaderboard`.
- Per-person streak: `longest_streak`.
- Half-month split with style classification: `frontload_vs_cram`.
- Mean delay aggregation: `lazy_logger_score`.
