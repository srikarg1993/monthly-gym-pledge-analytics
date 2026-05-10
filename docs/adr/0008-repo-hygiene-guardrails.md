# 0008 — Repo hygiene guardrails (forbid-known-junk + scratch convention)

- Status: Accepted
- Date: 2026-05-09

## Context

While removing the `mutmut` tooling (commits `6fe2541` → `4b44de4`), a 53 KB
binary `.mutmut-cache` SQLite file accidentally landed in the cleanup commit.
Root cause: the `.gitignore` entry was removed at the same time as the tool,
but the on-disk cache file wasn't deleted first. A subsequent `git add -A`
swept the binary in. Windows then file-locked the cache, requiring a
follow-up `git rm --cached` commit to untrack it.

Three problems surfaced:

1. **No automated guard.** `.gitignore` is a single line of defense. If the
   line is removed before the file is, the safety net is gone.
2. **No documented procedure** for removing a tool / dependency. The "delete
   artifact first, gitignore last" order is non-obvious.
3. **No convention for scratch / experimental work.** Engineers (human or
   agent) had no obvious place to put one-off scripts and intermediate
   output, so they tended to land at the repo root or inside `gym_pledge/`.

## Decision

Three additive guardrails:

1. **Pre-commit name-based block.** A new local hook
   [`scripts/forbid_known_junk.py`](../../scripts/forbid_known_junk.py) blocks
   known cache / scratch / generated artifacts by exact name, path prefix,
   and suffix \u2014 independent of `.gitignore` state. The
   `pre-commit/pre-commit-hooks` `check-added-large-files` hook (max 100 KB)
   is also enabled as a generic size backstop, along with
   `check-case-conflict`, `mixed-line-ending`, and `detect-private-key`.

2. **Documented removal procedure.** New skill
   [`docs/skills/removing-a-tool.md`](../skills/removing-a-tool.md) codifies
   the safe order of operations: stop processes → delete artifacts → uninstall
   → update config → update docs → update gitignore LAST → verify diff →
   stage explicitly (no `git add -A`) → run pre-commit → commit.

3. **`.scratch/` convention.** New skill
   [`docs/skills/repo-hygiene.md`](../skills/repo-hygiene.md) defines what's
   allowed at the repo root and establishes `.scratch/` (gitignored, blocked
   by `forbid-known-junk`) as the canonical home for ad-hoc experimentation.
   The `agents.md` §10 pre-commit gate gains a fifth audit dimension
   ("Diff-hygiene audit") that requires `git status --short` + `git diff --stat`
   review before staging.

## Consequences

**Positive**
- The exact `.mutmut-cache` mistake cannot recur \u2014 either the size hook
  (>100 KB) or the name hook (`.mutmut-cache` in `FORBIDDEN_NAMES`) catches
  it independently of gitignore state.
- Tool removal is now a checklist rather than improvisation, which reduces
  the chance of secret leaks (the same class of mistake that produced the
  GCP key incident in commit `10d976f`).
- New files have a clear place to go; the root stays clean.

**Negative**
- One more pre-commit hook to maintain. Adding a new tool with its own
  cache requires updating `FORBIDDEN_NAMES` / `FORBIDDEN_PREFIXES` in
  `scripts/forbid_known_junk.py`.
- The size threshold (100 KB) may need tuning if we ever legitimately
  need to commit a larger fixture. The escape hatch is the `ALLOWED`
  set in `forbid_known_junk.py`.

## Alternatives considered

- **Server-side push protection only.** GitHub's secret scanning blocks
  known token formats, but there's no equivalent for "binary cache files
  the project knows about". The local hook fills that gap and runs before
  the commit even exists.
- **`git lfs` for large files.** Overkill for a single-developer Streamlit
  dashboard with no real binary assets.
- **Make the hook part of CI instead of pre-commit.** CI catches the
  problem after the bad commit already exists, requiring a follow-up
  cleanup commit. Pre-commit catches it before the SHA is ever created.

## Related

- Skill: [`docs/skills/removing-a-tool.md`](../skills/removing-a-tool.md)
- Skill: [`docs/skills/repo-hygiene.md`](../skills/repo-hygiene.md)
- `agents.md` §10 (pre-commit gate)
- Memory: `/memories/repo/no-source-mutating-tools.md`
- Incident commits: `6fe2541` (introduced bug), `4b44de4` (untracked the file)
