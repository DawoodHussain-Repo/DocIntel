# Quick Start Guide

## Running the Backend

### Option 1: From backend directory (recommended)
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Using the quick run script
```powershell
cd backend
.\venv\Scripts\Activate.ps1
.\run.ps1
```

### Option 3: From root directory
```powershell
.\start-backend.ps1
```

## Running the Frontend

```powershell
cd frontend
npm run dev
```

## Important Notes

### Module Imports Fixed
All imports now work correctly when running from the `backend` directory:
- No more `ModuleNotFoundError: No module named 'backend'`
- Imports use relative paths (e.g., `from config import config`)
- `sys.path` manipulation in `main.py` ensures proper resolution

### Uvicorn Benefits
- **Hot reload**: Code changes automatically restart the server
- **Better performance**: ASGI server optimized for async
- **Standard practice**: Industry standard for FastAPI apps

## Troubleshooting

### If you get import errors:
1. Make sure you're in the `backend` directory
2. Activate the virtual environment
3. Use `uvicorn main:app --reload` (not `python main.py`)

### If port 8000 is busy:
```powershell
# Change port in .env
BACKEND_PORT=8001

# Or specify directly
uvicorn main:app --port 8001 --reload
```

## Development Workflow

1. **Start backend** (terminal 1):
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   uvicorn main:app --reload
   ```

2. **Start frontend** (terminal 2):
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Access the app**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Next Steps

1. ✅ Rotate your Groq API key
2. ✅ Update `.env` with new key
3. ✅ Test the application
4. ✅ Push to GitHub: `git push -f origin main`
