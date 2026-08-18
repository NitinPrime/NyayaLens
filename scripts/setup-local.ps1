# NyayaLens — Local setup (no Docker)
# Run from repo root:  .\scripts\setup-local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "NyayaLens local setup" -ForegroundColor Cyan
Write-Host "Repository: $Root"

# Ensure .env exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example"
}

# Python virtual environment
$venvPath = Join-Path $Root ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\python.exe"
$pip = Join-Path $venvPath "Scripts\pip.exe"

Write-Host "Installing Python dependencies..."
& $pip install -q -e packages/schemas
& $pip install -q -r apps/api/requirements.txt

# Frontend dependencies
Write-Host "Installing frontend dependencies..."
Set-Location (Join-Path $Root "apps\web")
npm install
Set-Location $Root

# Data directory
New-Item -ItemType Directory -Force -Path (Join-Path $Root "data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root "uploads") | Out-Null

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "Start the app with:  .\scripts\start-local.ps1" -ForegroundColor Yellow
