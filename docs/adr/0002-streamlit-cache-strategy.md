# ADR 0002: Streamlit cache TTL of 60 s for Google Sheets reads

- **Status**: Accepted
- **Date**: 2026-05-05
- **Tags**: data, performance, caching

## Context

Every Streamlit interaction (sidebar click, dropdown change) reruns the entire
script top-to-bottom. Without caching, every rerun would issue fresh
`gspread.open_by_key().get_all_values()` calls, which:

1. Costs latency (~0.5-2s per call).
2. Risks tripping Google Sheets API quota.
3. Produces flicker on heavy pages.

Counter-pressure: participants want their submissions to appear in the
dashboard within seconds, not after a hard refresh.

## Decision

Wrap `read_google_sheet_as_df`, `get_users`, and `get_data` with
`@st.cache_data(ttl=60, show_spinner=False)`. Within a 60-second window, every
rerun reuses the cached DataFrame.

## Consequences

### Positive
- Dashboard interactions feel instant.
- API quota usage stays well below limits.
- `show_spinner=False` keeps the UI quiet.

### Negative
- Up to a 60-second lag between a workout being logged and it appearing on the
  dashboard.
- Mitigation: users can force a fresh read via Streamlit's "Clear cache" menu
  item, or developers can call `st.cache_data.clear()`.

### Neutral
- Cache is per-process. A multi-replica deployment would have separate caches
  per replica — not currently relevant (single-process Streamlit).

## Alternatives considered

- **No cache**: rejected — quota and latency cost.
- **`ttl=300`**: rejected — too stale for the social pressure dynamics of the
  pledge.
- **`ttl=10`**: rejected — too chatty during interactive sessions.
