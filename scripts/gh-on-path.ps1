# Adds the GitHub CLI install dir to the current session's PATH if missing.
# Use with dot-sourcing so the change persists in your shell:
#   . .\scripts\gh-on-path.ps1
$ghDir = "C:\Program Files\GitHub CLI"
if ((Test-Path $ghDir) -and ($env:Path -notlike "*$ghDir*")) {
    $env:Path = "$ghDir;$env:Path"
    Write-Host "Added $ghDir to PATH for this session."
}
