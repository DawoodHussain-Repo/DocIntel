# DocIntel — Enterprise Legal Document Processing Pipeline

An AI-powered legal document analysis system built with LangGraph, FastAPI, and Next.js.

## Architecture

- **Backend**: Python + FastAPI
- **Agentic Core**: LangGraph + LangChain
- **Vector DB**: ChromaDB (local, persistent)
- **Persistence**: SQLite (via LangGraph SqliteSaver)
- **PDF Parsing**: Unstructured.io
- **Frontend**: Next.js 14 (App Router)
- **Streaming**: Server-Sent Events (SSE)
- **LLM**: OpenAI-compatible models (configurable)

## Features

✅ PDF ingestion with heading-aware chunking  
✅ Semantic search over legal documents  
✅ LangGraph agent with tool calling  
✅ Persistent conversation history (survives restarts)  
✅ Real-time streaming responses with SSE  
✅ Citation tracking with [Page X] references  
✅ Drag-and-drop file upload  

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key (or compatible endpoint)

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and choose your LLM provider:
   
   **For Groq (default)**:
   ```
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.1-70b-versatile
   ```
   
   **For LM Studio (local testing)**:
   ```
   LLM_PROVIDER=lmstudio
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LMSTUDIO_MODEL=local-model
   ```
   
   Note: Make sure LM Studio is running with a model loaded before using `lmstudio` provider.

3. **Run the backend**:
   ```bash
   cd backend
   python main.py
   ```
   
   Backend will start on `http://localhost:8000`

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run the development server**:
   ```bash
   npm run dev
   ```
   
   Frontend will start on `http://localhost:3000`

## Usage

### 1. Upload a Contract

- Drag and drop a PDF file into the left pane, or click to browse
- The system will parse, chunk, and index the document
- You'll see the document appear in the "Uploaded Documents" list

### 2. Ask Questions

- Type your question in the chat input (right pane)
- Press Enter to send (Shift+Enter for new line)
- Watch the agent:
  - Call the `search_legal_clauses` tool (shown as amber badge)
  - Stream the response token-by-token
  - Include [Page X] citations for every claim

### 3. Conversation Persistence

- Your conversation is saved to `docintel_memory.db`
- Refresh the page — your history persists (same session)
- Restart the backend — your history still persists

## API Endpoints

### `POST /api/upload_contract`

Upload and process a PDF contract.

**Request**:
```bash
curl -X POST http://localhost:8000/api/upload_contract \
  -F "file=@contract.pdf"
```

**Response**:
```json
{
  "status": "success",
  "file": "contract.pdf",
  "chunks_indexed": 42,
  "collection": "legal_docs"
}
```

### `GET /api/chat/stream`

Stream chat responses via SSE.

**Request**:
```bash
curl "http://localhost:8000/api/chat/stream?query=What%20are%20the%20payment%20terms?&thread_id=550e8400-e29b-41d4-a716-446655440000"
```

**Response** (SSE stream):
```
event: tool_call
data: {"tool": "search_legal_clauses", "query": "payment terms"}

event: token
data: {"text": "The"}

event: token
data: {"text": " payment"}

event: done
data: {"finish_reason": "stop"}
```

## Demo Script (Interview Acceptance Criteria)

Run these 5 checks to verify the system is interview-ready:

1. **Upload a PDF**: Drag-and-drop a legal contract → verify chunk count returned
2. **Ask about a clause**: "What are the indemnification obligations?" → verify tool call badge appears, then streams answer with [Page X] citations
3. **Ask about missing clause**: "What is the refund policy?" → verify response: "This clause is not present in the document."
4. **Refresh browser**: Re-ask previous question → verify conversation history persists
5. **Restart backend**: Kill and restart `python main.py`, send a message → verify SqliteSaver restored the thread

## Project Structure

```
/docintel
  /backend
    main.py              # FastAPI app with upload + streaming endpoints
    ingestion.py         # PDF parsing, chunking, embedding, ChromaDB upsert
    agent.py             # LangGraph agent with tools and checkpointer
    tools.py             # search_legal_clauses tool
    checkpointer.py      # SqliteSaver initialization
  /frontend
    /app
      page.tsx           # Main layout (dual-pane)
      layout.tsx         # Root layout
      globals.css        # Tailwind styles
      /components
        UploadPane.tsx   # Left pane: upload + doc list
        ChatPane.tsx     # Right pane: chat interface with SSE
  requirements.txt       # Pinned Python dependencies
  .env.example           # Environment template
  README.md              # This file
```

## Configuration

All configuration is via `.env`:

```bash
# LLM Provider: "groq" or "lmstudio"
LLM_PROVIDER=groq

# Groq Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# LM Studio Configuration (local testing)
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=local-model

# Storage
CHROMA_PERSIST_DIR=./chroma_db
SQLITE_DB_PATH=./docintel_memory.db

# Server
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
```

### Switching Between Providers

**Use Groq (cloud)**:
```bash
LLM_PROVIDER=groq
```

**Use LM Studio (local)**:
```bash
LLM_PROVIDER=lmstudio
```

Make sure LM Studio is running with a model loaded before switching to `lmstudio`.

## Troubleshooting

**ChromaDB collection empty error**:
- The agent will respond: "No documents have been indexed yet. Please upload a contract first."

**CORS errors**:
- Ensure `FRONTEND_URL` in `.env` matches your frontend URL
- Default: `http://localhost:3000`

**Conversation not persisting**:
- Check that `docintel_memory.db` exists in the backend directory
- Verify `thread_id` is being passed correctly (check browser console)

**PDF parsing fails**:
- Ensure the file is a valid PDF (MIME type check)
- Check file size is under 20MB
- Review backend logs for detailed error messages

## License

MIT
