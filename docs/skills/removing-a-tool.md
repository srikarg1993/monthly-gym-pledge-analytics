# Skill: Removing a tool or dependency

Use when: you're ripping out a library, dev tool, or workflow that touches
multiple files (config, requirements, docs, gitignore, CI, caches on disk).

This skill exists because of the **`.mutmut-cache` incident** (commit
`6fe2541`, fixed in `4b44de4`): the gitignore entry for the cache was
removed in the same change that removed the tool, but the on-disk cache
file wasn't deleted first, so the next `git add -A` swept a 53 KB binary
into the commit. Don't repeat it.

---

## The order matters

Do the steps in this exact order. Each step is reversible up until the
commit.

1. **Stop the tool's processes.**
   - `Get-Process python | Where-Object { $_.Path -like "*\.venv\*" }` to
     see what venv-resident processes are running.
   - Kill anything that could hold a file lock on the tool's caches.
2. **Delete on-disk artifacts FIRST, while gitignore still protects them.**
   - Caches: `.tool-cache`, `.tool-cache.db`, `coverage.xml`, etc.
   - Output dirs: `mutants/`, `htmlcov/`, `dist/`, etc.
   - Run `Remove-Item ... -Recurse -Force -ErrorAction SilentlyContinue`.
   - If a file is locked (Windows), use `git rm --cached <path>` later
     instead of fighting the lock.
3. **Uninstall from the venv.**
   `uv pip uninstall <pkg>` (or `pip uninstall -y <pkg>` if not on uv).
4. **Remove from `requirements*.txt` and `pyproject.toml`.**
   - Delete the line in `requirements-dev.txt` (or runtime requirements).
   - Delete any `[tool.<name>]` block in `pyproject.toml`.
   - Delete any tool-specific addopts / config keys.
5. **Remove from CI workflows.**
   - `.github/workflows/*.yml`: drop install / run steps.
   - `.pre-commit-config.yaml`: drop the hook entry.
6. **Remove from docs.**
   - `agents.md` skills index entry, if any.
   - `docs/skills/<tool>.md`, if it exists.
   - `README.md` references.
   - Any ADR that adopted it: do NOT delete the ADR — supersede it with a
     new ADR explaining why we removed the tool. ADRs are append-only.
7. **Update `.gitignore` LAST.**
   - Keep the gitignore entry for the tool's cache as a permanent guard
     (a future `pip install` mistake won't accidentally commit cruft).
   - Add a comment: `# <tool> is no longer used; entry kept as a guard`.
8. **Verify the diff before staging.**
   - `git status --short` — scan for unexpected files.
   - `git diff --stat` — scan for binaries (look for `Bin <n> -> <m>`).
   - Specifically: **no files with extensions `.db`, `.sqlite`,
     `.cache`, `.bin`, `.pyc`** unless you put them there on purpose.
9. **Stage explicitly.** Avoid `git add -A` / `git add .` for cleanup
   commits. Use `git add <path1> <path2>` to keep the change auditable.
10. **Run the pre-commit gate.**
    `pre-commit run --all-files` — the local `forbid-known-junk` hook
    will block known cache patterns even if you forgot step 2.
11. **Commit + push.** Include a short note in the commit body about why
    the tool was removed (audit trail).

---

## What the safety net catches

Even if you skip steps 2 / 8 / 9, the repo's pre-commit gate has two
backstops:

- **`check-added-large-files`** (max 100 KB) blocks any file bigger than
  100 KB. Most cache binaries trip this.
- **`forbid-known-junk`** (local hook, [`scripts/forbid_known_junk.py`](../../scripts/forbid_known_junk.py))
  blocks files by name / prefix / suffix regardless of size. New cache
  patterns can be added to its `FORBIDDEN_*` lists.

If neither hook catches your case, that's a hook gap. **Update the hook
in the same PR as the cleanup commit.**

---

## When not to use this skill

- Removing a single line from `requirements.txt` for a runtime-only lib
  with no caches and no integration → just edit + test + commit.
- Disabling a feature without removing the dependency → no cleanup
  needed.

---

## Related

- [`docs/skills/repo-hygiene.md`](repo-hygiene.md) — what's allowed at the repo root, scratch convention.
- [`docs/skills/commit-messages.md`](commit-messages.md) — for the commit body.
- [`docs/adr/0006-archive-folder-policy.md`](../adr/0006-archive-folder-policy.md) — why we don't delete historical code.
