# DocIntel API Reference

Complete reference for all backend HTTP endpoints.

**Base URL:** `http://localhost:8000`

---

## Authentication

No authentication is required for local development. In production, add an API key or OAuth layer in front of the FastAPI app.

---

## Endpoints

### `GET /health`

Health check for uptime monitoring.

**Response** `200 OK`:

```json
{
  "status": "success",
  "data": {
    "service": "docintel-backend",
    "version": "1.0.0"
  },
  "message": null
}
```

---

### `POST /api/upload_contract`

Upload and index a PDF contract into the vector database.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | PDF file (max 20 MB) |

**Validation Rules:**
- MIME type must be `application/pdf`
- File must begin with `%PDF-` magic bytes
- File size must not exceed `MAX_FILE_SIZE_MB` (default: 20 MB)

**Success Response** `201 Created`:

```json
{
  "status": "success",
  "data": {
    "file": "contract.pdf",
    "chunks_indexed": 42,
    "collection": "legal_docs"
  },
  "message": null
}
```

**Error Responses:**

| Status | Code | When |
|--------|------|------|
| `400` | `INVALID_MIME_TYPE` | File is not a PDF |
| `400` | `INVALID_PDF_SIGNATURE` | File bytes don't match PDF magic header |
| `413` | `FILE_TOO_LARGE` | File exceeds size limit |
| `422` | `EMPTY_DOCUMENT` | PDF contains no extractable text |
| `500` | `PDF_PARSE_FAILED` | Unstructured failed to parse the PDF |

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/upload_contract \
  -F "file=@contract.pdf"
```

---

### `GET /api/chat/stream`

Stream agent responses as Server-Sent Events.

**Query Parameters:**

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `query` | string | ✅ | 1–2000 chars | Natural language question |
| `thread_id` | string | ✅ | Valid UUID | Conversation thread identifier |

**Response:** `200 OK` with `Content-Type: text/event-stream`

**Error Responses:**

| Status | Code | When |
|--------|------|------|
| `400` | `EMPTY_QUERY` | Query is blank |
| `400` | `QUERY_TOO_LONG` | Query exceeds `MAX_QUERY_LENGTH` |
| `400` | `INVALID_THREAD_ID` | `thread_id` is not a valid UUID |
| `503` | `AGENT_NOT_READY` | Agent hasn't finished initializing |

**cURL Example:**

```bash
curl -N "http://localhost:8000/api/chat/stream?query=What+are+the+payment+terms&thread_id=550e8400-e29b-41d4-a716-446655440000"
```

---

## SSE Event Specification

The chat stream emits exactly three event types:

### `tool_call`

Emitted when the agent invokes a tool before answering.

```
event: tool_call
data: {"tool": "search_legal_clauses", "query": "payment terms"}
```

### `token`

Emitted for each streamed text token of the response.

```
event: token
data: {"text": "The"}
```

### `done`

Final event — signals the stream is complete. Always emitted.

```
event: done
data: {"finish_reason": "stop", "error": null}
```

On error:

```
event: done
data: {"finish_reason": "error", "error": "Streaming failed: connection reset"}
```

---

## Response Envelopes

### Success Envelope

All non-streaming endpoints return:

```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional human-readable note"
}
```

### Error Envelope

All error responses return:

```json
{
  "status": "error",
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "details": { ... }
}
```

---

## Error Code Reference

| Code | HTTP | Description |
|------|------|-------------|
| `INVALID_MIME_TYPE` | 400 | Uploaded file is not a PDF |
| `INVALID_PDF_SIGNATURE` | 400 | File bytes don't start with `%PDF-` |
| `FILE_TOO_LARGE` | 413 | File exceeds configured size limit |
| `EMPTY_DOCUMENT` | 422 | PDF contains no extractable text |
| `PDF_PARSE_FAILED` | 500 | Unstructured library failed to parse |
| `UPLOAD_PROCESSING_FAILED` | 500 | Generic upload pipeline failure |
| `CHUNKING_FAILED` | 500 | Failed to create chunks from PDF |
| `EMPTY_QUERY` | 400 | Chat query is blank after trimming |
| `QUERY_TOO_LONG` | 400 | Query exceeds `MAX_QUERY_LENGTH` |
| `INVALID_THREAD_ID` | 400 | Thread ID is not a valid UUID |
| `AGENT_NOT_READY` | 503 | Agent hasn't initialized yet |
| `VALIDATION_ERROR` | 422 | Request body failed Pydantic validation |
| `HTTP_ERROR` | varies | Generic HTTP error |
| `INTERNAL_SERVER_ERROR` | 500 | Unhandled exception (details hidden) |
