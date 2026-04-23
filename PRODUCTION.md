# DocIntel — Production Deployment Guide

This guide covers deploying DocIntel to production with proper hardening, monitoring, and operational best practices.

---

## Pre-Deployment Checklist

### Security

- [ ] All secrets are in `.env` (never in code)
- [ ] `.env` is in `.gitignore`
- [ ] `GROQ_API_KEY` is set (if using Groq)
- [ ] `CORS_ORIGINS` is restricted to your frontend domain
- [ ] `ALLOWED_HOSTS` is restricted to your backend domain
- [ ] Rate limiting is enabled (default: 10/min upload, 30/min chat)
- [ ] Agent timeout is configured (`AGENT_TIMEOUT_SECONDS=120`)

### Logging

- [ ] `LOG_FORMAT=json` (for log aggregators)
- [ ] `LOG_LEVEL=INFO` (or `WARNING` for production)
- [ ] Logs are shipped to a centralized system (Datadog, CloudWatch, Loki, etc.)

### Infrastructure

- [ ] ChromaDB persistence directory is backed up
- [ ] SQLite database is backed up
- [ ] Health check endpoint (`/health`) is monitored
- [ ] Uptime monitoring is configured
- [ ] Error alerting is configured

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Backend
LLM_PROVIDER=groq
GROQ_MODEL=llama-3.1-70b-versatile
LLM_TEMPERATURE=0.2
BACKEND_PORT=8000
CORS_ORIGINS=https://your-frontend-domain.com
ALLOWED_HOSTS=your-backend-domain.com,localhost
MAX_FILE_SIZE_MB=20
MAX_QUERY_LENGTH=2000
AGENT_TIMEOUT_SECONDS=120

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Persistence
CHROMA_PERSIST_DIR=./chroma_db
SQLITE_DB_PATH=./docintel_memory.db
WORKSPACE_DIR=./workspace

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Frontend
NEXT_PUBLIC_BACKEND_URL=https://your-backend-domain.com
```

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Quick Start)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/DocIntel.git
cd DocIntel

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Build and start services
docker-compose up -d

# 4. Check health
curl http://localhost:8000/health

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Deployment

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run with production server
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start
```

---

## Monitoring

### Health Check

The `/health` endpoint returns deep health checks:

```json
{
  "status": "success",
  "data": {
    "service": "docintel-backend",
    "version": "1.0.0",
    "checks": {
      "chromadb": "ok",
      "agent": "ok",
      "checkpointer": "ok"
    }
  },
  "message": "healthy"
}
```

**Status Codes:**
- `200` — All checks passed
- `503` — One or more checks failed (degraded state)

### Structured Logs

All logs are JSON-structured when `LOG_FORMAT=json`:

```json
{
  "event": "agent_stream_completed",
  "level": "info",
  "timestamp": "2026-04-23T10:00:00Z",
  "request_id": "abc-123",
  "run_id": "def-456",
  "thread_id": "ghi-789",
  "token_count": 245,
  "tool_call_count": 1
}
```

**Key Events to Monitor:**

| Event | Level | Description |
|-------|-------|-------------|
| `application_startup_completed` | INFO | Backend started successfully |
| `application_startup_failed` | ERROR | Backend failed to start |
| `agent_stream_timeout` | WARNING | Agent exceeded timeout |
| `agent_stream_failed` | ERROR | Agent crashed during streaming |
| `upload_processing_failed` | ERROR | PDF processing failed |
| `rate_limit_exceeded` | WARNING | User hit rate limit |
| `unhandled_exception` | ERROR | Unexpected error |

### Metrics to Track

1. **Request Metrics:**
   - Request rate (requests/second)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)

2. **Agent Metrics:**
   - Agent invocation count
   - Average token count per response
   - Tool call frequency
   - Timeout rate

3. **Upload Metrics:**
   - Upload success rate
   - Average chunks per document
   - Processing time

4. **Resource Metrics:**
   - CPU usage
   - Memory usage
   - Disk usage (ChromaDB, SQLite)

---

## Backup Strategy

### ChromaDB

```bash
# Backup
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Restore
tar -xzf chroma_backup_YYYYMMDD.tar.gz
```

### SQLite

```bash
# Backup
sqlite3 docintel_memory.db ".backup docintel_memory_backup_$(date +%Y%m%d).db"

# Restore
cp docintel_memory_backup_YYYYMMDD.db docintel_memory.db
```

**Recommended Schedule:**
- Daily backups retained for 7 days
- Weekly backups retained for 4 weeks
- Monthly backups retained for 12 months

---

## Scaling

### Horizontal Scaling

DocIntel can be scaled horizontally with the following considerations:

1. **Backend:**
   - Run multiple backend instances behind a load balancer
   - Share ChromaDB and SQLite via network storage (NFS, EFS)
   - Use sticky sessions for SSE streaming

2. **Frontend:**
   - Run multiple frontend instances behind a load balancer
   - No shared state required

### Vertical Scaling

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB

**Recommended for Production:**
- CPU: 4 cores
- RAM: 8GB
- Disk: 100GB (depends on document volume)

---

## Troubleshooting

### Backend Won't Start

1. Check logs: `docker-compose logs backend`
2. Verify environment variables: `cat .env`
3. Check health: `curl http://localhost:8000/health`

**Common Issues:**
- Missing `GROQ_API_KEY` → Set in `.env`
- Port 8000 already in use → Change `BACKEND_PORT`
- ChromaDB permission error → Check directory permissions

### Agent Timeouts

If you see frequent `agent_stream_timeout` events:

1. Increase `AGENT_TIMEOUT_SECONDS` (default 120)
2. Check LLM provider latency
3. Reduce `SEARCH_RESULT_LIMIT` (default 3)

### High Memory Usage

ChromaDB and embedding models are memory-intensive:

1. Monitor memory usage: `docker stats`
2. Increase container memory limits
3. Consider using a smaller embedding model

### Rate Limit Errors

If legitimate users hit rate limits:

1. Adjust limits in `main.py`:
   - Upload: `@limiter.limit("10/minute")`
   - Chat: `@limiter.limit("30/minute")`
2. Implement user-based rate limiting (requires authentication)

---

## Security Hardening

### HTTPS

Always use HTTPS in production:

```bash
# Using Nginx as reverse proxy
server {
    listen 443 ssl;
    server_name your-backend-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Firewall Rules

- Allow inbound: 443 (HTTPS), 22 (SSH)
- Block inbound: 8000 (backend), 3000 (frontend)
- Use reverse proxy for public access

### Secrets Management

Never commit secrets to git:

```bash
# .gitignore
.env
*.db
chroma_db/
workspace/
```

Use a secrets manager in production:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

---

## Maintenance

### Log Rotation

Configure log rotation to prevent disk exhaustion:

```bash
# /etc/logrotate.d/docintel
/var/log/docintel/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

### Database Maintenance

**SQLite:**
```bash
# Vacuum to reclaim space
sqlite3 docintel_memory.db "VACUUM;"

# Analyze for query optimization
sqlite3 docintel_memory.db "ANALYZE;"
```

**ChromaDB:**
- No maintenance required
- Monitor disk usage
- Backup regularly

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/DocIntel/issues
- Documentation: See `docs/` folder
- Architecture: See `CLAUDE.md`
