# Start DocIntel Backend

Write-Host "🚀 Starting DocIntel Backend..." -ForegroundColor Cyan

Set-Location backend
& .\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
