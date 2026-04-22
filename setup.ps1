# DocIntel Setup Script for Windows PowerShell

Write-Host "🚀 DocIntel Setup Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file. Please edit it with your API keys." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

# Backend Setup
Write-Host "📦 Setting up Backend..." -ForegroundColor Cyan
Set-Location backend

# Check if venv exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r ..\requirements.txt

Write-Host "✅ Backend setup complete!" -ForegroundColor Green
Write-Host ""

# Return to root
Set-Location ..

# Frontend Setup
Write-Host "📦 Setting up Frontend..." -ForegroundColor Cyan
Set-Location frontend

Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Write-Host "✅ Frontend setup complete!" -ForegroundColor Green
Write-Host ""

# Return to root
Set-Location ..

Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with your Groq API key" -ForegroundColor White
Write-Host "2. Start backend:  cd backend && .\venv\Scripts\Activate.ps1 && python main.py" -ForegroundColor White
Write-Host "3. Start frontend: cd frontend && npm run dev" -ForegroundColor White
Write-Host ""
