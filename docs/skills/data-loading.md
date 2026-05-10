# Skill: Touching Google Sheets I/O, caching, or `clean()`

Trigger: a new sheet column needs to be exposed; the dedupe rules change;
the cache TTL changes; auth issues come up.

## The boundary

`gym_pledge/data/source.py` is the **only** module that talks to Google
Sheets. Nothing else imports `gspread` or `google.oauth2`. UI code calls
`get_data()` or `get_users()`; metrics code receives a DataFrame.

## Auth

Service-account credentials live in `.streamlit/secrets.toml` under the
`[gcp_service_account]` table. The file is gitignored. Read via
`st.secrets["gcp_service_account"]`. Never accept credentials as function
arguments, never log them, never write them to disk.

## Adding a new column from the sheet

1. Add the column name to the Google Form / sheet.
2. In `clean()` (`source.py`), add a derivation step. Always operate on a
   `.copy()` and return a new DataFrame.
3. Add a default for missing values (`pd.NA`, `0`, etc.) so old rows don't
   break.
4. Update `tests/test_source.py` to assert the column is present and typed
   correctly.
5. Update the **Domain model** table in [`agents.md`](../../agents.md#L130).

## Dedupe rules

Workouts are deduped per `(name, workout_date)` keeping the latest
`timestamp`. The dedupe path:

```python
df = df.sort_values("timestamp", ascending=True)
df = df.drop_duplicates(subset=["name", "workout_date"], keep="last")
```

The `ascending=True` + `keep="last"` pair is intentional and produces a
deterministic result. Do not flip either flag without an ADR.

## Cache TTL

Default 60 s on `read_google_sheet_as_df`, `get_users`, `get_data`. See
[ADR 0002](../adr/0002-streamlit-cache-strategy.md). Changing the TTL is an
ADR-worthy change.

To force a fresh read in dev: call `st.cache_data.clear()` or use
Streamlit's "Clear cache" menu.

## Error handling

I/O errors at the boundary **must** be surfaced to the user via
`st.warning(...)` + `st.exception(e)`. Pure analytical code further down
the stack should let exceptions propagate.

## Tests

Cover any change to `clean()` or `normalize_bool` in
`tests/test_source.py` with a synthetic DataFrame — never hit the live
Google Sheets API in tests.
