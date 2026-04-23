# DocIntel System Architecture

## Overview

DocIntel is an AI-powered legal document intelligence system that ingests PDF contracts, indexes them as vector embeddings, and provides citation-grounded Q&A through a LangGraph agent with real-time streaming.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client (Browser)                          │
│                                                                     │
│   ┌──────────────┐                    ┌──────────────────────────┐  │
│   │  UploadPane   │                    │       ChatPane           │  │
│   │  (Drag & Drop)│                    │  (SSE Streaming Chat)    │  │
│   └──────┬───────┘                    └───────────┬──────────────┘  │
│          │ POST /api/upload_contract              │ GET /api/chat/  │
│          │ multipart/form-data                    │ stream?query=   │
└──────────┼────────────────────────────────────────┼─────────────────┘
           │                                        │
           ▼                                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend (Uvicorn)                     │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐  │
│  │  Upload Service   │  │            Chat Service                  │  │
│  │  ────────────────│  │  ──────────────────────────────────────  │  │
│  │  • MIME validate  │  │  • Thread ID validation                 │  │
│  │  • Magic byte chk │  │  • Query validation                    │  │
│  │  • Size limit     │  │  • SSE event formatting                │  │
│  └────────┬─────────┘  └──────────────┬───────────────────────────┘  │
│           │                           │                              │
│           ▼                           ▼                              │
│  ┌─────────────────┐      ┌───────────────────────────┐             │
│  │   Ingestion      │      │     LangGraph Agent       │             │
│  │  ─────────────── │      │  ───────────────────────  │             │
│  │  • PDF parsing   │      │  • System prompt grounding│             │
│  │  • Heading-aware │      │  • Tool routing           │             │
│  │    chunking      │      │  • Streaming response     │             │
│  │  • Embedding     │      │  • Checkpointed state     │             │
│  └────────┬─────────┘      └──────────┬────────────────┘             │
│           │                           │                              │
│           ▼                           ▼                              │
│  ┌──────────────────────────────────────────────────┐                │
│  │              ChromaDB (Single Client)             │                │
│  │              Persistent Vector Store              │                │
│  └──────────────────────────────────────────────────┘                │
│                                                                      │
│  ┌──────────────────────────────────────────────────┐                │
│  │          SQLite (AsyncSqliteSaver)                │                │
│  │          Conversation Checkpoints                 │                │
│  └──────────────────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### Frontend (Next.js 15 + React 19)

| Component | Responsibility |
|-----------|---------------|
| `page.tsx` | Root page — orchestrates hooks, passes props to panes |
| `UploadPane.tsx` | Drag-and-drop upload UI, document list display |
| `ChatPane.tsx` | Message rendering, SSE streaming display, chat input |
| `useChatStream.ts` | Manages message state, SSE consumption, session storage |
| `useContractUpload.ts` | Upload API call, loading/error state |
| `useThreadId.ts` | Generates and persists UUID thread ID in sessionStorage |
| `useUploadedDocuments.ts` | Manages document list with localStorage persistence |
| `lib/api.ts` | All `fetch()` calls to the backend |
| `lib/sse.ts` | Low-level SSE frame parser |
| `lib/types.ts` | TypeScript interfaces shared across frontend |
| `lib/config.ts` | Frontend configuration constants |

### Backend (FastAPI + LangGraph)

| Module | Responsibility |
|--------|---------------|
| `main.py` | FastAPI app initialization, CORS, security headers, error handlers, lifespan |
| `config.py` | Single source of truth for all environment variables |
| `agent.py` | LangGraph `StateGraph` definition, model selection, tool binding |
| `ingestion.py` | PDF parsing (Unstructured fast strategy), heading-aware chunking with recursive text splitting, embedding, ChromaDB upsert |
| `tools.py` | `search_legal_clauses` tool with ChromaDB query |
| `prompts.py` | Versioned system prompts with anti-hallucination rules |
| `checkpointer.py` | AsyncSqliteSaver singleton lifecycle |
| `models.py` | Pydantic schemas for all API contracts |
| `errors.py` | Structured `AppError` exception class |
| `services/chat_service.py` | SSE event formatting, streaming orchestration |
| `services/upload_service.py` | Upload validation, temp file management, ingestion |

---

## Data Flow

### Document Ingestion Flow

```
PDF File
  │
  ▼
Upload Service (validate MIME, magic bytes, size)
  │
  ▼
Save to temp workspace directory (UUID filename)
  │
  ▼
Unstructured partition_pdf(strategy="fast") → structured elements
  │
  ▼
Heading-aware chunking with recursive text splitting
  │
  ├─ Detect Title/Header elements → section boundaries
  │
  ├─ Apply RecursiveTextSplitter with semantic separators:
  │    • Section breaks (\n\n\n)
  │    • Paragraph breaks (\n\n)
  │    • Sentence endings (. )
  │    • Clause separators (; )
  │    • List items (, )
  │
  └─ Add configurable overlap for context preservation
  │
  ▼
SentenceTransformer.encode() → embeddings
  │
  ▼
ChromaDB.upsert(ids, documents, embeddings, metadatas)
  │
  ▼
Cleanup temp file → return chunk count
```

### Chat Query Flow

```
User Query + Thread ID
  │
  ▼
Chat Service (validate query, validate UUID)
  │
  ▼
LangGraph agent.astream_events()
  │
  ├─── Agent decides to call tool ──► search_legal_clauses(query)
  │                                        │
  │                                        ▼
  │                                   ChromaDB.query()
  │                                        │
  │                                        ▼
  │                                   Formatted results with
  │                                   page numbers & headings
  │                                        │
  │    ◄── Tool result fed back ──────────┘
  │
  ▼
Agent generates response with [Page X] citations
  │
  ▼
SSE stream: tool_call → token → token → ... → done
```

---

## LangGraph Agent Topology

```
                    ┌─────────┐
                    │  START   │
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
              ┌────│  Agent   │────┐
              │    │  (LLM)   │    │
              │    └─────────┘    │
              │                    │
         has tool_calls       no tool_calls
              │                    │
              ▼                    ▼
         ┌─────────┐         ┌─────────┐
         │  Tools   │         │   END   │
         │  Node    │         └─────────┘
         └────┬────┘
              │
              └──────► back to Agent
```

**Nodes:**
- `agent` — Invokes the LLM with system prompt + conversation history + tool results
- `tools` — Executes tool calls (currently: `search_legal_clauses`)

**Edges:**
- `agent → tools` — When the LLM emits tool calls
- `agent → END` — When the LLM produces a final answer
- `tools → agent` — After tool execution, feed results back

---

## Persistence Strategy

| Data | Storage | Lifetime |
|------|---------|----------|
| Vector embeddings | ChromaDB (`./chroma_db/`) | Permanent (survives restarts) |
| Conversation state | SQLite (`./docintel_memory.db`) | Permanent (survives restarts) |
| Thread ID | Browser `sessionStorage` | Per browser tab session |
| Chat messages (display) | Browser `sessionStorage` | Per browser tab session |
| Uploaded doc list | Browser `localStorage` | Permanent (per browser) |
| Uploaded PDF files | Temp workspace dir, deleted after processing | Transient |

---

## Security Model

### Backend Security

| Measure | Implementation |
|---------|---------------|
| CORS | Restricted to configured `CORS_ORIGINS` |
| Trusted Hosts | `TrustedHostMiddleware` with `ALLOWED_HOSTS` |
| Security Headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` |
| File Validation | MIME type check + PDF magic byte verification |
| File Size Limit | Configurable via `MAX_FILE_SIZE_MB` |
| Query Length Limit | Configurable via `MAX_QUERY_LENGTH` |
| Temp File Safety | UUID-named files, cleaned up in `finally` block |
| Error Information | Internal details hidden in 500 responses |
| Secrets | All sensitive values in `.env`, never in source |

### Frontend Security

| Measure | Implementation |
|---------|---------------|
| Client-side validation | PDF MIME type check before upload |
| SSE parsing | All `event.data` parsed inside try/catch |
| No eval/innerHTML | React's built-in XSS protection |

---

## Dependency Graph

```
main.py
  ├── config.py (env vars)
  ├── agent.py
  │     ├── config.py
  │     ├── checkpointer.py → config.py
  │     ├── prompts.py
  │     └── tools.py → config.py
  ├── services/
  │     ├── chat_service.py → config.py, errors.py, models.py
  │     └── upload_service.py → ingestion.py, models.py, errors.py, config.py
  ├── ingestion.py → config.py, errors.py
  ├── models.py
  └── errors.py
```

Dependencies flow **inward only**: Routes → Services → Tools/Repos → DB. No circular imports.
