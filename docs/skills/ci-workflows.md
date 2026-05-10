# Skill: Adding or modifying a GitHub Actions workflow

Use this skill when adding a new workflow under `.github/workflows/` or
modifying an existing one (CI, CodeQL, stale, release, etc.).

## Repo-specific conventions

- All workflows live in `.github/workflows/` and use **lowercase**
  filenames (`ci.yml`, `codeql.yml`, `stale.yml`).
- Triggers we use: `push` (branches `main` + `p2f`), `pull_request`,
  `schedule` (UTC cron), `workflow_dispatch` for manual runs.
- Default runner: `ubuntu-latest`. Don't switch to Windows/macOS without a
  reason — billing minutes are 2× / 10× respectively.
- Python version: pinned to `3.11` everywhere (matches `pyproject.toml`).
- Dep install: use **`astral-sh/setup-uv@v7`** + `uv pip install -r
  requirements-dev.txt`. Don't use `pip install` directly — uv is faster
  and the cache is wired up.
- Action versions: pin to a major (`@v5`, `@v9`, `@v4`). Dependabot will
  PR upgrades weekly; review the changelog before merging.

## Pre-flight checklist

Before adding a workflow, ask:

1. **Is there already a job in `ci.yml` that should host this step?** If
   the new check just wraps a Python command (lint, test, type-check),
   add a step to `ci.yml` rather than creating a new file.
2. **Does it need elevated permissions?** The default `GITHUB_TOKEN` has
   read-only contents. If you need to push commits, open PRs, or write
   issues/PR comments, add a `permissions:` block at the workflow or job
   level. Grant only what's needed.
3. **Will it run on PRs from forks?** Forked PRs get a read-only token
   even if you grant write — assume secrets and write actions won't run
   for them. Use `pull_request_target` only with extreme care (security
   risk: runs in the base-repo context with secrets).
4. **Does the new check need to be a required status check?** If yes,
   after the first run lands, add it under branch protection (Settings →
   Rules → `protect-main`).

## Template — Python job

```yaml
name: <workflow-name>

on:
  push:
    branches: [main, p2f]
  pull_request:

jobs:
  <job-name>:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Create venv and install deps
        run: |
          uv venv
          uv pip install -r requirements-dev.txt

      - name: Run the thing
        run: uv run <command>
```

## Template — Scheduled cleanup job

```yaml
name: <name>

on:
  schedule:
    - cron: "0 9 * * *"   # daily 09:00 UTC
  workflow_dispatch:

permissions:
  issues: write
  pull-requests: write

jobs:
  ...
```

Cron is **UTC**, not local. America/Chicago is UTC-6 (CST) or UTC-5 (CDT).

## Verifying a new workflow

1. Push the workflow on a feature branch first; check the Actions tab.
2. Run `gh workflow run <name>` (or use the **Run workflow** button) to
   trigger `workflow_dispatch` manually if the trigger is `schedule:`.
3. Use `scripts/ci-status.ps1` to tail logs after push.
4. If the workflow needs to be a required check on `main`, after it runs
   once add it to the ruleset (see `docs/backlog.md` Tier-1 →
   "Branch protection").

## Common gotchas

- **Required check name = job name**, not workflow name. `Analyze (python)`
  is the matrix-expanded job name from CodeQL, not the workflow filename.
- **Caching across workflows is per-key.** Don't reuse the same key from
  `ci.yml` in another workflow — they evict each other.
- **`actions/cache` requires Node 20+** (will be Node 24 in mid-2026).
  Pin `@v4` for now.
- **Windows runners need `shell: pwsh`** for PowerShell or `shell: bash`
  for Git-Bash. Default on Linux is bash.
- **Don't echo secrets.** GitHub auto-masks known secrets in logs but only
  if they came from `secrets.*` — string-built tokens leak.

## See also

- [`docs/backlog.md`](../backlog.md) — Tier-1, Tier-2, Tier-3 CI/CD items
- [`scripts/ci-status.ps1`](../../scripts/ci-status.ps1) — quick CI log tail
- [`scripts/README.md`](../../scripts/README.md) — gh CLI helpers
