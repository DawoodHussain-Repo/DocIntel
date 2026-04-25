# DocIntel Startup Performance Guide

## Understanding Startup Time

DocIntel's backend initialization involves several steps that can affect startup time, especially on first run.

### Typical Startup Times

| Scenario | Expected Time | What's Happening |
|----------|--------------|------------------|
| **First Run** | 30-60 seconds | Downloading embedding model (~80MB) from HuggingFace |
| **Subsequent Runs** | 5-10 seconds | Loading cached model from disk |
| **With Fast SSD** | 3-5 seconds | Faster model loading from local cache |

## Startup Phases

The backend goes through these initialization phases:

### 1. Configuration Validation (< 1 second)
- Loads environment variables from `.env`
- Validates required settings
- Checks for missing configuration

### 2. ChromaDB Initialization (1-2 seconds)
- Opens persistent vector database
- Creates collections if needed
- Validates database integrity

### 3. SQLite Checkpointer (< 1 second)
- Opens conversation memory database
- Initializes async connection pool

### 4. Embedding Model Pre-warming (5-30 seconds)
**This is the main bottleneck on first startup!**

- **First Run:** Downloads `all-MiniLM-L6-v2` model (~80MB) from HuggingFace
- **Subsequent Runs:** Loads cached model from `~/.cache/torch/sentence_transformers/`
- Model is loaded into memory for fast inference

### 5. LLM Connection (1-2 seconds)
- Initializes connection to Groq or LM Studio
- Validates API credentials
- Tests connectivity

## Why Pre-warm Models?

**Before optimization:**
- Models loaded on first request (lazy loading)
- First user experiences 30+ second delay
- Subsequent requests are fast

**After optimization:**
- Models loaded during startup
- All requests are fast from the start
- Better user experience

## Optimizing Startup Time

### 1. Pre-download Embedding Model

Run this once to download the model before first startup:

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model downloaded and cached!")
```

### 2. Use Fast Storage

- Install DocIntel on SSD (not HDD)
- Model loading is I/O intensive
- SSD can reduce startup time by 50%

### 3. Keep Model Cache

Don't delete `~/.cache/torch/sentence_transformers/`

This directory contains:
- Downloaded embedding models
- Tokenizer files
- Model configuration

Size: ~80-100MB per model

### 4. Use Local LLM (LM Studio)

If using LM Studio:
- Ensure it's running before starting DocIntel
- Local LLM = no network latency
- Faster than cloud APIs (Groq)

### 5. Disable Reload in Production

Development mode uses `reload=True` which watches for file changes:

```python
# Development (slower startup)
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Production (faster startup)
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=4)
```

## Monitoring Startup

The backend logs each initialization phase:

```json
{"event": "application_startup_started", "version": "1.0.0"}
{"event": "configuration_validated"}
{"event": "chromadb_initialization_started"}
{"event": "chromadb_initialized", "persist_dir": "./chroma_db"}
{"event": "checkpointer_initialization_started"}
{"event": "checkpointer_initialized", "db_path": "./docintel_memory.db"}
{"event": "embedding_model_preload_started", "model": "all-MiniLM-L6-v2"}
{"event": "embedding_model_preload_completed"}
{"event": "llm_preload_started", "provider": "lmstudio"}
{"event": "llm_preload_completed"}
{"event": "application_startup_completed", "startup_time_seconds": 8.42}
```

Watch for:
- `embedding_model_preload_started` → `embedding_model_preload_completed` (longest phase)
- `startup_time_seconds` in final log (total time)

## Troubleshooting Slow Startup

### Issue: Startup takes > 2 minutes

**Possible Causes:**
1. **Slow internet connection** - Model download is slow
2. **HDD instead of SSD** - Model loading is I/O bound
3. **Antivirus scanning** - Scanning downloaded model files
4. **Low memory** - System swapping to disk

**Solutions:**
- Pre-download model (see above)
- Move to SSD
- Add exception for `~/.cache/torch/` in antivirus
- Close memory-intensive applications

### Issue: "Failed to download model"

**Possible Causes:**
- No internet connection
- HuggingFace is down
- Firewall blocking downloads

**Solutions:**
1. Check internet connection
2. Try manual download:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   ```
3. Use alternative model (update `.env`):
   ```env
   EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L3-v2
   ```

### Issue: "LLM connection failed"

**For Groq:**
- Check `GROQ_API_KEY` in `.env`
- Verify API key is valid
- Check Groq service status

**For LM Studio:**
- Ensure LM Studio is running
- Check `http://localhost:1234` is accessible
- Verify model is loaded in LM Studio

## Production Deployment

For production, consider:

### 1. Docker with Pre-warmed Image

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Pre-download embedding model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application
COPY . /app
WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Health Check with Readiness Probe

```yaml
# kubernetes/deployment.yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30  # Wait for model loading
  periodSeconds: 10
```

### 3. Multiple Workers

```bash
# Use multiple workers for better throughput
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Note:** Each worker loads its own embedding model (4 workers = 4x memory usage)

## Summary

| Optimization | Impact | Effort |
|--------------|--------|--------|
| Pre-download model | High (30s → 5s first run) | Low |
| Use SSD | Medium (5s → 3s) | Medium |
| Disable reload in prod | Low (saves 1-2s) | Low |
| Docker pre-warmed image | High (consistent fast startup) | Medium |
| Multiple workers | High (better throughput) | Low |

**Recommended for Development:**
- Pre-download model once
- Use SSD if available
- Accept 5-10s startup time

**Recommended for Production:**
- Docker with pre-warmed image
- Multiple workers
- Health check with readiness probe
- Monitor startup time in logs
