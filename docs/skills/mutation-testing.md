# Skill: Mutation testing with mutmut

Use this skill when you suspect tests are passing without actually
exercising the logic they claim to cover, or when adding new tests to a
data-layer function and want to know if they're meaningful.

## Why

Line / branch coverage answers "did this code run?" Mutation testing
answers "would my tests notice if this code were broken?" — a much
stronger signal.

## One-time setup

`mutmut` is in `requirements-dev.txt`. Pinned `<3` because mutmut 3 is
WSL-only on Windows (upstream issue
[boxed/mutmut#397](https://github.com/boxed/mutmut/issues/397)).

```powershell
uv pip install -r requirements-dev.txt
```

## Run a focused mutation pass

Mutating the entire codebase takes a long time. Always scope to one file:

```powershell
$env:PYTHONIOENCODING = "utf-8"      # mutmut prints emojis; cp1252 will crash
$env:PYTHONUTF8 = "1"
$env:PYTHONPATH = "gym_pledge"        # tests rely on this sys.path layout
$pyExe = (Resolve-Path .\.venv\Scripts\python.exe).Path

& $pyExe -m mutmut run `
    --paths-to-mutate gym_pledge/data/metrics.py `
    --runner "`"$pyExe`" -m pytest -x -q --no-cov tests/test_metrics.py tests/test_audit_edge_cases.py"
```

Notes on the runner string:
- The absolute path to `python.exe` is required — bare `python` hits the
  Microsoft Store stub on a clean Windows install.
- `-x` stops at the first failing test (faster mutant kill).
- `--no-cov` skips coverage to avoid slow per-mutant overhead.
- Pass only the tests that exercise the mutated file. Running the full
  suite for every mutant burns hours.

## Read results

```powershell
.\.venv\Scripts\python.exe -m mutmut results | Out-File -Encoding utf8 mutmut-results.txt
Get-Content mutmut-results.txt
```

Mutmut reports four buckets:

| Bucket | Meaning | Action |
|--------|---------|--------|
| Killed | Some test caught the mutation | Good — these don't need attention |
| Survived | No test caught the mutation | **Real test gap** — investigate |
| Suspicious | Tests took unusually long to fail | Usually flaky timing; can ignore |
| Untested / skipped | Mutant in code not exercised by the chosen tests | Either run more tests or accept it |

Inspect a survived mutant's diff:

```powershell
.\.venv\Scripts\python.exe -m mutmut show <id>
```

## What surviving mutants usually mean

From the 2026-05-09 baseline run on `gym_pledge/data/metrics.py`:

- **Operator flips** (`&` → `|`, `==` → `!=`, `>` → `>=`): means there
  is no test that distinguishes the two. Add a test with input near the
  boundary that would behave differently under each operator.
- **Constant flips** (`fillna(0)` → `fillna(1)`): means no test asserts
  the exact filled value. Tests assert something looser (e.g. dtype
  only). Add an exact-equality assertion.
- **Identifier renames** (`out["foo"]` → `out["XXfooXX"]`): means tests
  never read that column. The column might be unused — verify, then
  either delete it from the function or add a test that reads it.

## When to bother

Mutation testing is too slow for CI. Run it manually:

- After adding a new function in `data/*` — once you have happy-path +
  edge-case tests, run mutmut to find the gaps.
- Before locking in a behavior — if the user says "this is the way it
  should work", run mutmut to make sure the tests actually pin the
  behavior.
- During a quarterly test-quality audit — pick one file at a time.

Don't add it to the pre-commit gate or to CI. Multi-minute runs on every
push are not worth it for this repo.

## Cleanup

Mutmut writes `.mutmut-cache` (SQLite, ~50 KB) and `mutmut-results.txt`
in the repo root. Both are gitignored. Delete them between runs if you
want a fresh baseline:

```powershell
Remove-Item .mutmut-cache, mutmut-results.txt -ErrorAction SilentlyContinue
```

## See also

- [`docs/skills/testing.md`](testing.md) — pytest, fixtures, coverage gate
- [`pyproject.toml`](../../pyproject.toml) — `[tool.mutmut]` config block
