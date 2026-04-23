# DocIntel — AI-Powered Legal Document Intelligence

An enterprise-grade legal document analysis system. Upload PDF contracts, ask natural-language questions, and receive citation-grounded answers powered by a LangGraph agent with semantic search.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+ · FastAPI · Uvicorn |
| Agentic Core | LangGraph · LangChain · OpenAI-compatible LLMs |
| Vector DB | ChromaDB (persistent, local) |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| Persistence | SQLite (LangGraph AsyncSqliteSaver) |
| Frontend | Next.js 15 (App Router) · React 19 · Tailwind CSS |
| Streaming | Server-Sent Events (SSE) |

## Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm`
- **Groq API key** ([get one here](https://console.groq.com/keys)) — or a running LM Studio instance

## Quick Start

### 1. Clone & Configure

```powershell
git clone https://github.com/DawoodHussain-Repo/DocIntel.git
cd DocIntel
cp .env.example .env
```

Edit `.env` and set your Groq API key:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

### 2. Install Dependencies

**Backend** (Python):

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

**Frontend** (Node.js):

```powershell
cd frontend
npm install
cd ..
```

### 3. Run the Application

> **⚠️ Important:** Always activate the backend virtual environment before starting the backend. Without it, Python will not find the installed packages and the server will crash with import errors.

Open **two separate terminals** from the project root:

**Terminal 1 — Backend:**

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

**Terminal 2 — Frontend:**

```powershell
cd frontend
npm run dev
```

Or use the convenience script that opens both terminals automatically:

```powershell
.\start.ps1
```

The app will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs

## Usage

1. **Upload a contract** — Drag-and-drop a PDF into the left panel (or click Browse)
2. **Ask questions** — Type a question in the chat panel and press Enter
3. **Get cited answers** — The agent searches the document, streams its response, and cites every claim with `[Page X]` references
4. **Conversation persists** — Refresh the browser or restart the backend; your thread survives via SQLite

## Configuration

All settings are managed through `.env`. See [`.env.example`](.env.example) for the full list. Key options:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `groq` | `groq` or `lmstudio` |
| `GROQ_API_KEY` | — | Required when using Groq |
| `GROQ_MODEL` | `llama-3.1-70b-versatile` | Model identifier |
| `LLM_TEMPERATURE` | `0.2` | Response randomness (0–1) |
| `BACKEND_PORT` | `8000` | FastAPI server port |
| `MAX_FILE_SIZE_MB` | `20` | Upload size limit |
| `CHUNK_SIZE` | `1000` | Maximum characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks for context preservation |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | `json` | Log output format (`json` for production, `console` for development) |

## Project Structure

```
DocIntel/
├── backend/
│   ├── main.py              # FastAPI app, lifespan, CORS, error handlers
│   ├── agent.py             # LangGraph agent graph definition
│   ├── ingestion.py         # PDF parsing, chunking, embedding, ChromaDB upsert
│   ├── tools.py             # search_legal_clauses tool
│   ├── config.py            # Single source of truth for all env vars
│   ├── checkpointer.py      # AsyncSqliteSaver lifecycle
│   ├── models.py            # Pydantic request/response schemas
│   ├── prompts.py           # System prompts (versioned)
│   ├── errors.py            # Structured error types
│   ├── services/
│   │   ├── chat_service.py  # SSE streaming orchestration
│   │   └── upload_service.py# Upload validation + ingestion
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Root page (dual-pane layout)
│   │   ├── layout.tsx       # HTML shell, fonts, metadata
│   │   └── globals.css      # Design system
│   ├── components/
│   │   ├── ChatPane.tsx     # Chat interface with SSE streaming
│   │   └── UploadPane.tsx   # Document upload + index list
│   ├── hooks/               # useChatStream, useContractUpload, etc.
│   └── lib/                 # API client, SSE parser, types, config
├── docs/
│   ├── api.md               # Full API reference
│   ├── architecture.md      # System architecture & diagrams
│   └── design.md            # UI design system documentation
├── start.ps1                # Launch both servers (separate terminals)
├── .env.example             # Environment variable template
└── README.md                # ← You are here
```

## Documentation

Detailed docs live in the [`docs/`](docs/) folder:

- **[API Reference](docs/api.md)** — Endpoints, schemas, SSE event spec, error codes
- **[Architecture](docs/architecture.md)** — System design, data flow, LangGraph topology
- **[Design System](docs/design.md)** — Color palette, typography, component catalog

## License

MIT
