# Architectural Decision Records

This directory captures the "why" behind structural decisions. Each ADR is
small, immutable once accepted, and dated.

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](0001-flat-package-layout.md) | Flat package layout under `gym_pledge/` | Accepted |
| [0002](0002-streamlit-cache-strategy.md) | Streamlit cache TTL of 60 s for Google Sheets reads | Accepted |
| [0003](0003-per-month-cutoff-overrides.md) | Per-month winner-cutoff overrides via config dict | Accepted |
| [0004](0004-timezone-via-app-time.md) | Centralize "now" via `app_time.py` and `APP_TIMEZONE` | Accepted |
| [0005](0005-unified-dark-visual-language.md) | Unified dark visual language for scorecard charts | Accepted |
| [0006](0006-archive-folder-policy.md) | `gym_pledge/00_Archive/` is read-only history | Accepted |
| [0007](0007-audit-cleanup-2026-05.md) | Audit pass — remove dead chart helpers and tighten type hints | Accepted |

## How to add an ADR

1. Copy `0000-template.md` to the next sequential number.
2. Fill in Context / Decision / Consequences / Alternatives.
3. Update the index table above.
4. Commit alongside the code change the ADR explains.
