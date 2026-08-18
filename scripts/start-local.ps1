# NyayaLens — Start API + frontend locally (no Docker)
# Run from repo root:  .\scripts\start-local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not (Test-Path (Join-Path $Root ".venv\Scripts\python.exe"))) {
    Write-Host "Run setup first:  .\scripts\setup-local.ps1" -ForegroundColor Red
    exit 1
}

Write-Host "Starting NyayaLens (local mode)" -ForegroundColor Cyan
Write-Host "  API:  http://localhost:8000"
Write-Host "  Web:  http://localhost:3000"
Write-Host "  Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "Press Ctrl+C in each terminal to stop." -ForegroundColor Yellow
Write-Host ""

# Start API in a new window
$apiCmd = "Set-Location '$Root\apps\api'; & '$Root\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd

Start-Sleep -Seconds 2

# Start frontend in a new window
$webCmd = "Set-Location '$Root\apps\web'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $webCmd

Write-Host "Started API and frontend in separate windows." -ForegroundColor Green
