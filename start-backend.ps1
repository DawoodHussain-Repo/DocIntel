# Start DocIntel Backend

Write-Host "🚀 Starting DocIntel Backend..." -ForegroundColor Cyan

Set-Location backend
& .\venv\Scripts\Activate.ps1
python main.py
