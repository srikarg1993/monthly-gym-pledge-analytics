# Skill: Repo hygiene

Use when: you're about to create a new file, especially at the repo root,
or when you're auditing what's there and wondering if something belongs.

The goal is a repo where every file at the root has an obvious reason to
be there, and where ad-hoc / temporary work doesn't pollute the tree.

---

## Allowed at the repo root

The root is reserved for top-level metadata that tools or humans expect
to find at the top:

| File / dir | Why it's allowed |
|---|---|
| `README.md` | GitHub renders it on the landing page |
| `agents.md`, `CLAUDE.md` | Agent system prompts (CLAUDE.md is a stub) |
| `pyproject.toml` | Python project metadata + tool config |
| `requirements.txt`, `requirements-dev.txt` | Pinned deps for Streamlit Cloud + dev |
| `.pre-commit-config.yaml` | Required at root by `pre-commit` |
| `.gitignore`, `.gitattributes` | Required at root by git |
| `start-app.sh` | Convenience launcher; documented in README |
| `.github/`, `.devcontainer/`, `.streamlit/`, `.claude/` | Tool-required locations |
| `.venv/`, `.ruff_cache/`, `.pytest_cache/`, `.coverage` | Local caches (gitignored) |
| `gym_pledge/`, `tests/`, `docs/`, `scripts/` | The four canonical source dirs |

If a new file doesn't fit one of these, it does **not** belong at the root.

## Forbidden at the repo root (and everywhere)

Caught by the pre-commit gate (see
[`scripts/forbid_known_junk.py`](../../scripts/forbid_known_junk.py)):

- Cache databases: `.mutmut-cache`, `.coverage`, `coverage.xml`,
  `mutmut-results.txt`
- OS junk: `.DS_Store`, `Thumbs.db`
- Compiled bytecode: `*.pyc`, `*.pyo`, `__pycache__/`
- Cache dirs: `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `htmlcov/`
- Scratch: `.scratch/`, `scratch/`, `*.scratch`, `*.tmp`

Adding a new tool with its own cache? Add it to the `FORBIDDEN_*` lists
in `forbid_known_junk.py` AND to `.gitignore`.

---

## Where new things go

| Kind of work | Goes in | Notes |
|---|---|---|
| New analytical function | [`gym_pledge/data/metrics.py`](../../gym_pledge/data/metrics.py) | See [`docs/skills/metrics.md`](metrics.md) |
| New chart | [`gym_pledge/ui/common.py`](../../gym_pledge/ui/common.py) | See [`docs/skills/charts.md`](charts.md) |
| New sidebar page | `gym_pledge/ui/<page>.py` | See [`docs/skills/ui-page.md`](ui-page.md) |
| New test | `tests/test_<module>.py` | See [`docs/skills/testing.md`](testing.md) |
| New skill / recipe | `docs/skills/<topic>.md` | Add it to the skills index in `agents.md` |
| New ADR | `docs/adr/NNNN-<slug>.md` | Use [`0000-template.md`](../adr/0000-template.md) |
| Helper / one-off script | `scripts/<name>.py` or `scripts/<name>.ps1` | Document in script's docstring / header |
| Generated data fixture | `tests/fixtures/` | Not at repo root |

---

## Scratch / temporary work convention

If you need to throw something on disk while exploring — a one-off script,
a dump of intermediate output, a hand-edited copy of a chart — put it in
`.scratch/` at the repo root. That directory is gitignored and the
pre-commit gate blocks anything inside it from being committed. You can
keep it indefinitely without polluting the tree.

```text
.scratch/                  # never committed
  prototype_chart.py
  sheet_dump_2026-05.csv
  notes.md
```

Don't:

- Drop scratch files at the repo root.
- Use `tests/` as scratch.
- Use `gym_pledge/00_Archive/` as scratch (see
  [`docs/adr/0006-archive-folder-policy.md`](../adr/0006-archive-folder-policy.md)).

---

## Audit checklist (run before any cleanup commit)

```powershell
# What does git think is in the diff?
git status --short
git diff --stat

# What's untracked in the working tree (sanity check the gitignore)?
git status --ignored --short | Select-String -Pattern "^!!"

# Anything weird at root?
Get-ChildItem -Force | Where-Object { -not $_.PSIsContainer } |
    Select-Object Name, Length, LastWriteTime
```

If any of these surface a file you don't recognize, find out where it
came from before committing.

---

## Related

- [`docs/skills/removing-a-tool.md`](removing-a-tool.md) — the safe order
  of operations for tool removal.
- [`docs/adr/0001-flat-package-layout.md`](../adr/0001-flat-package-layout.md)
  — why the source tree looks the way it does.
- [`docs/adr/0006-archive-folder-policy.md`](../adr/0006-archive-folder-policy.md)
  — why `gym_pledge/00_Archive/` exists and stays.
