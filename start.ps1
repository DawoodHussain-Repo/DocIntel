# DocIntel — Start Script
# Launches backend and frontend in separate terminal windows.
#
# IMPORTANT: The backend terminal automatically activates the Python
# virtual environment. If you run the backend manually instead, you
# MUST activate it yourself first:
#
#   cd backend
#   .\venv\Scripts\Activate.ps1
#   python main.py
#
# Without the venv active, Python will not find installed packages
# and the server will crash with import errors.

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host ""
Write-Host "  DocIntel Start" -ForegroundColor Cyan
Write-Host "  ==============" -ForegroundColor Cyan
Write-Host ""

# --- Backend (new terminal) ---
$backendCmd = @"
Set-Location '$ProjectRoot\backend'
& '.\venv\Scripts\Activate.ps1'
Write-Host ''
Write-Host '  Backend starting on http://localhost:8000' -ForegroundColor Green
Write-Host '  Press Ctrl+C to stop.' -ForegroundColor DarkGray
Write-Host ''
python main.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Write-Host "  [1/2] Backend terminal opened" -ForegroundColor Green

# --- Frontend (new terminal) ---
$frontendCmd = @"
Set-Location '$ProjectRoot\frontend'
Write-Host ''
Write-Host '  Frontend starting on http://localhost:3000' -ForegroundColor Green
Write-Host '  Press Ctrl+C to stop.' -ForegroundColor DarkGray
Write-Host ''
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "  [2/2] Frontend terminal opened" -ForegroundColor Green
Write-Host ""
Write-Host "  Open http://localhost:3000 in your browser." -ForegroundColor Cyan
Write-Host ""
