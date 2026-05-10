<#
.SYNOPSIS
  Print the latest GitHub Actions run(s) for a branch.

.DESCRIPTION
  Wraps `gh run list` and `gh run view` so you can check CI without
  remembering the gh syntax. If the latest run failed, also dumps the
  failing job's log tail.

.PARAMETER Branch
  Branch to inspect. Defaults to the current git branch.

.PARAMETER Limit
  How many runs to list. Defaults to 1.

.EXAMPLE
  .\scripts\ci-status.ps1
  .\scripts\ci-status.ps1 -Branch main
  .\scripts\ci-status.ps1 -Limit 5
#>
[CmdletBinding()]
param(
    [string]$Branch,
    [int]$Limit = 1
)

# Make sure gh is on PATH (winget installs to "C:\Program Files\GitHub CLI"
# which sometimes isn't picked up until a new shell is opened).
$ghDir = "C:\Program Files\GitHub CLI"
if ((Test-Path $ghDir) -and ($env:Path -notlike "*$ghDir*")) {
    $env:Path = "$ghDir;$env:Path"
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "gh CLI not found on PATH. Install it: winget install GitHub.cli"
    exit 1
}

if (-not $Branch) {
    $Branch = (git rev-parse --abbrev-ref HEAD).Trim()
}

Write-Host "CI runs for branch: $Branch" -ForegroundColor Cyan
gh run list --branch $Branch --limit $Limit `
    --json status,conclusion,name,displayTitle,databaseId,createdAt,url `
    --template '{{range .}}{{tablerow (printf "%s/%s" .status .conclusion) .name (timeago .createdAt) .displayTitle}}{{end}}'

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# If the most-recent run failed, dump the failing job's tail.
$latest = gh run list --branch $Branch --limit 1 --json conclusion,databaseId | ConvertFrom-Json
if ($latest -and $latest[0].conclusion -eq "failure") {
    Write-Host ""
    Write-Host "Latest run failed. Tail of failing logs:" -ForegroundColor Yellow
    gh run view $latest[0].databaseId --log-failed | Select-Object -Last 60
}
