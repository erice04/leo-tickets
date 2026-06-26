# Start LEO Tickets (single clean instance)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Stop anything already listening on port 5000
Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 2

if (-not (docker compose ps --status running -q db 2>$null)) {
    Write-Host "Starting PostgreSQL..."
    docker compose up db -d
    Start-Sleep -Seconds 5
}

$env:FLASK_APP = "app.py"
$env:FLASK_DEBUG = "0"
Write-Host "Starting app at http://127.0.0.1:5000"
python app.py
