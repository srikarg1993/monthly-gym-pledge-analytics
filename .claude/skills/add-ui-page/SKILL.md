---
name: add-ui-page
description: Add a new page/view to the Streamlit dashboard sidebar. Use when the user asks to "add a new tab", "add a page", "create a new view", or "add X to the sidebar".
---

# Add a new UI page

All pages live under `gym_pledge/ui/` and are wired into the sidebar in `gym_pledge/dashboard.py`.

## Steps

1. **Create `gym_pledge/ui/<page_name>.py`** exporting a `render(df, users, ...)` function.

   Conventions:
   - Accept the cleaned DataFrame from `data.source.get_data()` — don't re-fetch the sheet.
   - Use `app_time.now()` / `app_time.today()` for any "current" date; never `datetime.now()`.
   - Use `winner_cutoff_for_month(month)` from `config.globals` — never a hardcoded integer.
   - Pull shared styling/helpers from `gym_pledge/ui/common.py`.

2. **Register it in `dashboard.py`**:
   - Import the module at the top.
   - Add a label → callable entry to the sidebar navigation mapping.
   - To keep a page hidden from the sidebar (like `monthovermonth` and `personalization`), register it but exclude it from the visible-labels list.

3. **Style** using the existing dark theme — prefer CSS classes already defined in `gym_pledge/styles/theme.css` over inline styles.

4. **Test**:
   - For pure data transforms, add a test under `tests/` (see `tests/test_yearcalendar.py` as a template, especially the empty-df / None / unknown-person edge cases).
   - For pure rendering, exercise the page manually via the `run-app` skill.

## Checklist before shipping

- [ ] New page appears in the sidebar (or is intentionally hidden).
- [ ] Renders without error on an empty DataFrame.
- [ ] Renders without error when a selected person has no rows.
- [ ] No direct `datetime.now()` / `date.today()` calls — all routed through `app_time`.
- [ ] No hardcoded cutoff values — routed through `winner_cutoff_for_month`.
- [ ] `pytest tests/` still green.
