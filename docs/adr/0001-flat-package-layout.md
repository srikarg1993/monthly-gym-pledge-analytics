# ADR 0001: Flat package layout under `gym_pledge/`

- **Status**: Accepted
- **Date**: 2026-05-05
- **Tags**: structure, packaging

## Context

The repository started as a Jupyter notebook plus a single-file Streamlit
script. As the dashboard grew, two layouts were considered: a deeply nested
`gym_pledge_app/` package mirroring Django-style boundaries (`pages/`,
`metrics/`, `viz/`, `data/`, `assets/`) versus a flat package with a small
number of top-level subpackages.

The deeply nested layout exists in `gym_pledge/00_Archive/gym_pledge_app/`
as historical evidence.

## Decision

Use a flat layout: `gym_pledge/{config,data,ui,styles}/` plus
`dashboard.py` and `app_time.py` at the package root. UI pages each live as a
single module under `gym_pledge/ui/`. Chart factories are centralized in
`gym_pledge/ui/common.py`.

## Consequences

### Positive
- Imports are short and unambiguous (`from data.metrics import ...`).
- New contributors can locate a page in one click.
- Tests sit at the repo root in `tests/` and add `gym_pledge/` to `sys.path`
  themselves — no install step.

### Negative
- `ui/common.py` has grown past 2,500 LOC. Future pressure may force a split
  by chart family; that split needs its own ADR.

## Alternatives considered

- **Nested `gym_pledge_app/`**: rejected for over-abstraction at the current
  scale (~10 modules total).
- **`src/` layout**: rejected because it adds installation friction without
  benefit at this team size.
