# scripts/

Convenience scripts for the gym-pledge repo. None are required to run the
app — they're shortcuts for common dev tasks.

## `ci-status.ps1`

Print the latest GitHub Actions run for a branch, plus the failing job's log
tail if the run failed.

```powershell
# Current branch
.\scripts\ci-status.ps1

# Specific branch
.\scripts\ci-status.ps1 -Branch main

# Last 3 runs
.\scripts\ci-status.ps1 -Limit 3
```

Requires `gh` (GitHub CLI) on PATH and `gh auth login` completed once.

## `gh-on-path.ps1`

Helper to add the GitHub CLI to your PATH for the current session if winget
installed it but PowerShell hasn't picked it up yet.

```powershell
. .\scripts\gh-on-path.ps1
```
