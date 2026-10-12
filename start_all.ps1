# Start AuraMatch AI Agentic Dating Platform
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting AuraMatch AI — Agentic Dating Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"
$venvUvicorn = Join-Path $backendDir ".venv\Scripts\uvicorn.exe"

# Fallback to system uvicorn/python if local .venv doesn't exist
if (Test-Path $venvUvicorn) {
    $uvicornCmd = $venvUvicorn
    $uvicornArgs = "app.main:app --host 0.0.0.0 --port 8000 --reload"
} else {
    $uvicornCmd = "uvicorn"
    $uvicornArgs = "app.main:app --host 0.0.0.0 --port 8000 --reload"
}

# Start Backend
Write-Host "[1/2] Launching FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath $uvicornCmd `
    -ArgumentList $uvicornArgs `
    -WorkingDirectory $backendDir `
    -PassThru

# Start Frontend
Write-Host "[2/2] Launching Next.js Frontend on http://localhost:3000..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run dev" `
    -WorkingDirectory $frontendDir `
    -PassThru

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend API & Docs: http://localhost:8000/api/v1/docs" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
