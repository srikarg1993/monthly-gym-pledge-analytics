---
name: debug-sheets
description: Diagnose Google Sheets connection and data-loading issues — auth errors, empty DataFrames, missing users, "NaT" months. Use when the user reports "the app can't connect to the sheet", "data isn't loading", "leaderboard is empty", or sees `SpreadsheetNotFound` / `APIError` / `KeyError: 'gcp_service_account'`.
---

# Debug Google Sheets connectivity & data issues

Data flows: Google Sheet → `gym_pledge/data/source.py` (`read_google_sheet_as_df` → `clean` → `get_data`) → DataFrame → UI pages.

## Checklist (in order)

### 1. Credentials load

- `gym_pledge/.streamlit/secrets.toml` must exist and contain a `[gcp_service_account]` table with the full service-account JSON.
- If missing: `st.secrets["gcp_service_account"]` raises `KeyError`. Populate the file and restart Streamlit (it caches secrets per process).

### 2. Sheet access

- Open `gym_pledge/config/globals.py` and note `SPREADSHEET_ID` + `WORKSHEET_NAME`.
- Verify the service-account email (`client_email` in secrets.toml) is shared as **Viewer** on the target sheet.
- `gspread.exceptions.SpreadsheetNotFound` → wrong ID or not shared. `APIError 403` → not shared. `APIError 429` → quota — see section 6.

### 3. Worksheet / headers

- The Form Responses worksheet must have columns: `Timestamp`, `You are?`, `Workout date`, `Burnt >= 250 calories?`. `source.clean` raises `ValueError` if any are missing.
- The `Venmo Tracker` worksheet (used by `get_users`) must have a column whose header exactly matches the full-month-name format produced by `_month_label` in `source.py` (e.g., `"April 2026"`). A rename in the sheet silently returns an empty user list.

### 4. Empty / partial DataFrame symptoms

| Symptom                                    | Likely cause                                                    |
|--------------------------------------------|------------------------------------------------------------------|
| Leaderboard renders with zero rows         | No submissions, OR `get_users` returned empty and there are no rows for the current month either |
| Freshly submitted workout doesn't appear   | `get_data` / `get_users` are cached for 60s via `@st.cache_data`. Wait, or run `st.cache_data.clear()` from the Streamlit menu |
| Unparseable `Workout date` cells           | `clean()` converts them to `pd.NA` in the `month` column — they are filtered out of the month dropdown. If an "NaT" string is surfacing, check that `source.py` still uses `.where(month_period.notna(), pd.NA)` |
| One person missing from the leaderboard    | They aren't marked `"In"` in the month's column on `Venmo Tracker`, AND they have no submissions yet |
| Entry shows old value after user corrected it | Dedup keeps the latest timestamp via `sort_values("timestamp", ascending=True).drop_duplicates(..., keep="last")` in `source.clean()`. If this is mis-wired, corrections will be silently lost |

### 5. Quick repro in a shell

```python
from gym_pledge.data.source import read_google_sheet_as_df, clean, get_users
df_raw = read_google_sheet_as_df()
print(df_raw.shape, df_raw.columns.tolist())
df = clean(df_raw)
print(df.dtypes)
print(df["month"].value_counts(dropna=False))   # watch for "NaT"
print(get_users("2026-04"))
```

### 6. API quota / rate limits

`read_google_sheet_as_df`, `get_users`, and `get_data` are wrapped with `@st.cache_data(ttl=60)`, so a normal session hits the Sheets API roughly once per minute. If you see `APIError 429`:

- Confirm the decorators are still in place on all three in `gym_pledge/data/source.py`.
- Bump `ttl` (e.g., to `300`) while debugging — just remember to invalidate the cache when you want fresh data.
- Reduce rapid-fire interactions that invalidate caches by changing args (e.g., switching months frequently).

### 7. Timezone-related "wrong month" bugs

If a submission logged near midnight lands in the wrong month in the UI, the cause is almost always a mix of `datetime.now()` / `date.today()` calls that bypass `app_time.py`. Audit with:

```bash
grep -rn "datetime.now\|date.today" gym_pledge/
```

All such calls should route through `app_time.now()` / `app_time.today()`.
