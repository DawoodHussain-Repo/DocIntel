# DocIntel Backend

Production-grade FastAPI backend with LangGraph agent for legal document intelligence.

## Project Structure

```
backend/
├── api/                      # API layer
│   ├── middleware.py         # Request tracing, logging middleware
│   ├── routes/               # API route handlers (future)
│   └── dependencies/         # FastAPI dependencies (future)
├── core/                     # Core business logic
│   ├── agent.py              # LangGraph agent definition
│   ├── checkpointer.py       # Conversation persistence
│   ├── config.py             # Configuration management
│   ├── errors.py             # Custom exception classes
│   ├── ingestion.py          # PDF parsing and chunking
│   ├── models.py             # Pydantic schemas
│   ├── prompts.py            # System prompts
│   └── tools.py              # LangGraph tools
├── services/                 # Service layer
│   ├── chat_service.py       # SSE streaming orchestration
│   └── upload_service.py     # Upload validation and processing
├── utils/                    # Utility functions
│   └── logger.py             # Structured logging setup
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
└── Dockerfile                # Docker image definition
```

## Architecture Principles

1. **Layered Architecture:**
   - `main.py` → `services/` → `core/` → External dependencies
   - Strict dependency flow (no circular imports)

2. **Configuration:**
   - Single source of truth: `core/config.py`
   - All settings from environment variables
   - Validated at startup

3. **Logging:**
   - Structured JSON logs via `structlog`
   - Context propagation (request_id, run_id, thread_id)
   - No `print()` statements

4. **Error Handling:**
   - Custom `AppError` for business logic failures
   - Generic 500 responses (details logged internally)
   - Structured error envelope for all failures

## Setup

### Prerequisites

- Python 3.10+
- LM Studio running on http://localhost:1234 (or configure GROQ)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env with your settings
```

### Running

```bash
# Development
python main.py

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Configuration

See `../.env.example` for all available options.

Key settings:
- `LLM_PROVIDER`: `lmstudio` or `groq`
- `LOG_FORMAT`: `json` (production) or `console` (development)
- `AGENT_TIMEOUT_SECONDS`: Maximum agent execution time
- `MAX_FILE_SIZE_MB`: Upload size limit

## API Endpoints

- `POST /api/upload_contract` - Upload and index PDF
- `GET /api/chat/stream` - Stream agent responses (SSE)
- `GET /health` - Health check with sub-system status

See `../docs/api.md` for full API documentation.

## Development

### Adding New Features

1. Add Pydantic models to `core/models.py`
2. Add business logic to `core/` or `services/`
3. Add routes to `main.py` (or `api/routes/` for complex routes)
4. Add error codes to `core/errors.py`
5. Add structured logging at each stage

### Code Quality

- Follow `../CLAUDE.md` guidelines
- Use `structlog` for all logging
- Validate inputs at API boundary
- Handle errors gracefully
- Write docstrings for public functions

## Testing

```bash
# Run tests (when available)
pytest

# Type checking
mypy .

# Linting
ruff check .
```

## Deployment

See `../PRODUCTION.md` for production deployment guide.

### Docker

```bash
# Build image
docker build -t docintel-backend .

# Run container
docker run -p 8000:8000 --env-file ../.env docintel-backend
```

## Troubleshooting

### Import Errors

If you see import errors after reorganization:
```bash
# Ensure you're in the backend directory
cd backend

# Run from backend directory
python main.py
```

### LM Studio Connection

If agent fails to connect to LM Studio:
1. Ensure LM Studio is running
2. Check `LMSTUDIO_BASE_URL` in `.env`
3. Verify model is loaded in LM Studio
4. Check logs for connection errors

### ChromaDB Issues

If ChromaDB fails to initialize:
```bash
# Remove and recreate
rm -rf chroma_db/
# Restart backend (will recreate on startup)
```

## License

MIT
