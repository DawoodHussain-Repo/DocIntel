# Quick Installation Guide

## Automated Setup (Recommended)

Run the setup script from the project root:

```powershell
.\setup.ps1
```

This will:
- Create `.env` from `.env.example` if needed
- Set up Python virtual environment
- Install all Python dependencies
- Install all Node.js dependencies

## Manual Setup

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
cd ..
```

### Frontend

```powershell
cd frontend
npm install
cd ..
```

### Configure Environment

Edit `.env` and add your Groq API key:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_actual_key_here
```

## Running the Application

### Option 1: Use Start Scripts

**Terminal 1 - Backend:**
```powershell
.\start-backend.ps1
```

**Terminal 2 - Frontend:**
```powershell
.\start-frontend.ps1
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

## Verify Installation

1. Backend should be running on: `http://localhost:8000`
2. Frontend should be running on: `http://localhost:3000`
3. Visit `http://localhost:3000` in your browser

## Troubleshooting

### Python Dependencies Fail

Make sure you're in the virtual environment:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

### ChromaDB Issues

Delete the `chroma_db` folder and restart:
```powershell
Remove-Item -Recurse -Force chroma_db
```

### Port Already in Use

Change ports in `.env`:
```env
BACKEND_PORT=8001
```

And update frontend API calls in `frontend/app/components/*.tsx` to match.
