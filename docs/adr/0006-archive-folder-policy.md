# ADR 0006: `gym_pledge/00_Archive/` is read-only history

- **Status**: Accepted
- **Date**: 2026-05-05
- **Tags**: structure, repo-hygiene

## Context

The repository contains an `00_Archive/` subfolder under `gym_pledge/`
holding the original notebook (`gym_kitty_analysis_reviewed*.ipynb`), the
first single-file Streamlit script (`streamlit_app.py`,
`gym_kitty_app.py`), and an early nested package layout
(`gym_pledge_app/`). These are not imported by the live app and exist only
for historical reference.

Two failure modes were observed before this ADR:

1. New AI agents would attempt to refactor or delete archive files, breaking
   nothing in the live app but generating noisy diffs and lost history.
2. Cleanup PRs would propose removing the entire archive, throwing away
   useful provenance for ~zero size benefit.

## Decision

Treat `gym_pledge/00_Archive/` as immutable history:

- Do not import from it.
- Do not refactor, lint, or reformat it.
- Do not delete files inside it without an ADR explicitly proposing removal
  and approval from the maintainer.
- `pyproject.toml` `[tool.ruff]` excludes the archive from lint runs.

## Consequences

### Positive
- Provenance preserved.
- AI agents have a clear rule to follow.
- Live app surface area stays small in audits.

### Negative
- The archive contributes ~10k LOC to the repo. Acceptable: pure text, no
  binary blobs.

## Alternatives considered

- **Move to a separate `archive/` git branch**: rejected — discoverability
  cost outweighs the small repo-size win.
- **Delete entirely**: rejected — loses context for design decisions that
  predate the current modular layout.
