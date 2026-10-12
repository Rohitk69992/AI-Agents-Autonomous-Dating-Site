# Start AuraMatch AI Agentic Dating Platform
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting AuraMatch AI — Agentic Dating Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Start Backend
Write-Host "[1/2] Launching FastAPI Backend on http://localhost:8000..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "c:\Users\rohit\Downloads\datingSite\backend\.venv\Scripts\uvicorn.exe" `
    -ArgumentList "app.main:app --host 0.0.0.0 --port 8000 --reload" `
    -WorkingDirectory "c:\Users\rohit\Downloads\datingSite\backend" `
    -PassThru

# Start Frontend
Write-Host "[2/2] Launching Next.js Frontend on http://localhost:3000..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run dev" `
    -WorkingDirectory "c:\Users\rohit\Downloads\datingSite\frontend" `
    -PassThru

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  All services started!" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend API & Docs: http://localhost:8000/api/v1/docs" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
