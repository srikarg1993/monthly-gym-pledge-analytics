# Skill: Adding a new sidebar page

Trigger: the app needs a new top-level view (e.g., a "Streaks" page, an
"Awards" page).

## The recipe

1. **Create the module** at `gym_pledge/ui/<page>.py`.
2. **Define a single render function**:
   ```python
   def render(df: pd.DataFrame, **kwargs) -> None:
       st.title("My Page")
       ...
   ```
   - Returns `None`. Side effects only — this is a Streamlit page.
   - Accepts the cleaned workout DataFrame as the first positional arg.
   - Other dependencies (active users, current month) come in as kwargs.
3. **Wire into the sidebar** in `gym_pledge/dashboard.py`:
   - Import the module.
   - Add an entry to the page-routing dict.
   - To hide from the sidebar but keep accessible by deep link, follow the
     pattern of `monthovermonth.py` / `personalization.py`.
4. **Reuse chart factories** from `ui/common.py` rather than defining new
   Altair specs inline.
5. **Apply the visual design language** — same dark `#0B1220` background,
   same accent palette, same chip text pattern. See
   [`docs/skills/charts.md`](charts.md) and
   [ADR 0005](../adr/0005-unified-dark-visual-language.md).
6. **Honor the layering rules**: import from `data/*` and `ui/common.py`,
   not the other way around. See `agents.md` section 3.

## Tests

Render functions are not unit-tested; their pure data helpers (anything
prefixed `_build_`) **are**. Put those in `tests/test_<page>.py`.

## Reference

- Simple page: `gym_pledge/ui/about.py` (static content).
- Data-driven page: `gym_pledge/ui/leaderboard.py`.
- Most complex: `gym_pledge/ui/scorecard.py` — uses ~12 chart factories.
