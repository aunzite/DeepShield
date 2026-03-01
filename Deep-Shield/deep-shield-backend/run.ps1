# Run DeepShield backend (PowerShell)
# From repo root: .\deep-shield-backend\run.ps1
# Or from deep-shield-backend: .\run.ps1

$ErrorActionPreference = "Stop"
$backendDir = $PSScriptRoot

Set-Location $backendDir

# Use venv if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating .venv..." -ForegroundColor Cyan
    & .\.venv\Scripts\Activate.ps1
}

# Ensure dependencies
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found. Install Python and add it to PATH."
}
Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Green
python main.py
