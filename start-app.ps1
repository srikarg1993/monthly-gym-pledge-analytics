# Kill any process on port 8501 and start the Monthly Gym Pledge Streamlit app.
# Windows / PowerShell counterpart of start-app.sh — closes the
# cross-platform-parity gap flagged in the 2026-05-10 adversarial review (P2-13).

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Port = 8501

$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($existing) {
    $procIds = $existing | Select-Object -ExpandProperty OwningProcess -Unique
    Write-Host "Stopping process on port $Port (graceful): $procIds"
    foreach ($processId in $procIds) {
        try {
            Stop-Process -Id $processId -ErrorAction Stop
        } catch {
            Write-Warning "Could not stop ${processId}: $_"
        }
    }
    Start-Sleep -Seconds 2
    $still = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($still) {
        Write-Host "Process still alive — forcing termination."
        $still | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
    }
}

Write-Host "Starting app on http://localhost:$Port"
& ".\.venv\Scripts\streamlit.exe" run "gym_pledge\dashboard.py" --server.port $Port
