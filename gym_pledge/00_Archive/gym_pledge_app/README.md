# Gym Kitty Dashboard (refactored)

## Run
From the folder containing `gym_pledge_app/`:

```bash
cd gym_pledge_app
streamlit run app.py
```

## Notes
- Keep your existing `secrets/service_account.json` relative path the same as before.
- All data logic is in `data/` and `metrics/` (Streamlit-free and testable).
- UI pages live in `pages/`.
- Plot styling is centralized in `viz/`.
