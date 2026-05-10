# Skill: Writing high-signal commit messages

Trigger: about to run `git commit` on this repo.

## The format

```
<type>: <imperative summary, ≤ 72 chars>

<blank line>

<body — what changed and WHY, wrapped at ~72 chars>

<optional: bullet groups by area>

<optional: trailers — Refs:, Co-authored-by:, Closes:>
```

### Subject line

- Imperative mood: "Add", "Fix", "Refactor", "Remove" — not "Added", not "Adds".
- ≤ 72 characters. Hard cap.
- No trailing period.
- Lead with a `<type>:` prefix when the change is purely one of:
  - `feat:` — new user-visible capability
  - `fix:` — bug fix
  - `refactor:` — internal change, no behavior delta
  - `perf:` — measurable performance change
  - `test:` — tests only
  - `docs:` — docs / ADRs / skills only
  - `chore:` — tooling, deps, CI, repo hygiene
  - `style:` — visual / CSS only (charts qualify)
- For mixed commits, drop the prefix and write a clean imperative sentence.

### Body

- **Always** explain *why*, not just *what* — the diff already shows the *what*.
- Wrap at ~72 chars per line.
- Group related bullets under a heading when the commit touches multiple areas:
  ```
  Documentation
  - ...

  Code hygiene
  - ...

  Test coverage
  - ...
  ```
- Reference ADRs by number when relevant: `(see ADR 0005)`.
- Include any operator-visible side effect: cache TTL change, new env var,
  required `pip install`, breaking schema change.

### Trailers

- `Refs: #123` for issue links (we don't use issues yet, but reserve the slot).
- `Closes: #123` only when the commit fully closes an issue.
- `Co-authored-by: Name <email>` when pairing.
- `BREAKING CHANGE: <description>` on the last line of the body for any
  user-visible regression. Forces a major version bump in tooling that
  reads conventional commits.

## Examples

### Good

```
Modernize Lazy Logger bubble clusters with radial gradients

Match the dashboard's unified visual language (ADR 0005) by rendering
each bubble with an SVG <radialGradient> and a Gaussian-blur outer
glow. Add zone icon, count badge, and accent top-edge strip to each
card.

- LAZY_ZONES grew from 5-tuple to 6-tuple (added icon)
- 3 internal consumers updated to match
- Tests + ruff clean
```

### Bad

```
fixed lazy logger
```

Why bad: vague, lowercase, no body, doesn't say *why*.

## Don'ts

- **Don't fabricate test counts in the body.** If you write "73 passing,
  75 % coverage", you must have run `pytest --cache-clear` and
  `pytest --cov` in the current session and seen those exact numbers.
  When in doubt, omit the number rather than guess.
- **Don't summarize files that didn't change.** Diff stats already do that.
- **Don't include "🤖 Generated with Copilot" or similar attributions.**
  Use `Co-authored-by:` if relevant; otherwise the commit speaks for itself.
- **Don't squash unrelated changes** into one commit just to clear the
  working tree. Stage in groups; commit per logical unit.
- **Don't use shell heredocs or multi-line `-m` flags** in PowerShell —
  PSReadLine breaks on embedded quotes. Use `git commit -F path/to/msg.txt`
  for any message longer than ~5 lines, then **delete the temp file** in the
  same session.

## PowerShell-safe commit recipe

```powershell
$msg = @"
<type>: <subject>

<body line 1>
<body line 2>
"@
$msg | Out-File -Encoding utf8 .git\COMMIT_MSG.txt
git commit -F .git\COMMIT_MSG.txt
Remove-Item .git\COMMIT_MSG.txt    # clean up immediately
```

Or, for short single-line commits, plain `git commit -m "<subject>"` is fine.
