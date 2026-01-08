Monthly Gym Pledge Analytics
=============================

Overview
--------
This small Streamlit app tracks a monthly group fitness pledge. It reads workout submissions from a Google Form (Google Sheet), computes monthly leaderboards, streaks, winners and summary statistics, and renders a compact dashboard with charts and tables.

Quick goals
-----------
- Make the app easy to read and maintain.
- Keep UI code modular under `ui/`.
- Centralize shared helpers (see `ui/common.py`).
- Avoid breaking existing behavior while refactoring.

Files of interest
-----------------
- [dashboard.py](dashboard.py): main Streamlit entry and page routing.
- [ui/scorecard.py](ui/scorecard.py): Scorecard page (winners, summary tables, bubble chart).
- [ui/leaderboard.py](ui/leaderboard.py): Live leaderboard UI.
- [ui/logyourworkout.py](ui/logyourworkout.py): "Log my workout" CTA and page copy.
- [data/source.py](data/source.py): reading + cleaning raw sheet data.
- [data/metrics.py](data/metrics.py): leaderboard and metrics computations.
- [ui/common.py](ui/common.py): shared UI helpers (table renderer, plot styling).

Dependencies
------------
The app expects a Python environment with the following packages installed (minimum):

- Python 3.9+
- streamlit
- pandas
- altair
- matplotlib
- seaborn
- gspread
- google-auth

Install quickly with pip (preferably in a venv):

```bash
pip install streamlit pandas altair matplotlib seaborn gspread google-auth
```

Configuration / Google Sheet access
----------------------------------
1. The app reads data from a Google Sheet. Ensure the following secrets/config are available:
   - A service-account JSON with access to the sheet (placed in `secrets/service_account.json` or configured via `st.secrets`).
   - The Google Sheet must be shared with the service-account email.
2. Configure `config/globals.py` values only if you're changing which sheet or worksheet the app reads.

Run (development)
-----------------
From the `gym_pledge` directory run:

```bash
streamlit run dashboard.py
```

This will open the app in your browser. Use the sidebar to navigate pages.

What I changed (refactor highlights)
-----------------------------------
- Centralized the styled HTML table renderer in `ui/common.py` as `render_styled_table` and updated pages to use it.
- Replaced several wildcard imports with explicit imports to reduce namespace pollution.
- Added concise module docstrings for clarity in `data/metrics.py`, `data/source.py`, and several `ui/` modules.
- Improved the weekday bubble chart styling on the Scorecard page (single color, centered labels, dark-theme friendly).

Safety note
-----------
All changes were made to be low-risk and incremental. I did not alter core computations in `data/metrics.py` beyond organizing imports and adding docstrings. Still, please run the app locally to visually confirm behavior before deploying.

Next recommended steps
----------------------
- Create a `requirements.txt` (I can generate one from the codebase).
- Run the app locally and confirm visuals/behavior.
- If you approve, proceed with medium-risk refactors: extract repeated chart code into helpers, centralize CSS/card HTML.

Contributing / Contact
----------------------
If you'd like me to continue refactoring, tell me whether to:
- proceed with the medium-risk refactors now, or
- finish sweeping low-risk cleanups (remove remaining small duplicates, linting).

