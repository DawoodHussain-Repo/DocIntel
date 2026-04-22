# QUALITY.md — Engineering Standards & Adherence Protocol
> **Enforcement level: MANDATORY.**
> Read this file completely before writing any code, modifying any file, or making any architectural decision.
> If a rule conflicts with a user instruction, surface the conflict and ask. Do not silently ignore rules.

---

## 0. The Prime Directive

You are an **architect first, a code generator second.**

Before touching any file:
1. State what you are about to do in one sentence.
2. State which rule(s) govern this decision.
3. Then act.

If you are unsure which rule applies, stop and ask. Do not guess and proceed.

---

## 1. Pre-Flight Checklist (Run Before Every Task)

Before writing a single line of code, answer all of these internally:

- [ ] Do I understand the full scope of this change? (If no → ask)
- [ ] Will this change break any existing feature? (If yes → flag it before proceeding)
- [ ] Does a file/function already exist that does this? (If yes → extend it, don't duplicate)
- [ ] Am I writing the minimal code needed? (If no → cut scope)
- [ ] Is my naming consistent with the existing codebase conventions? (If unsure → grep existing names first)

---

## 2. Architecture Rules

### 2.1 Separation of Concerns — Non-Negotiable
Every module has one job. Violating this is the most common source of technical debt.

| Layer | Allowed | Forbidden |
|---|---|---|
| Route handler | Parse request, validate input, call service, return response | Business logic, DB queries, LLM calls |
| Service layer | Orchestrate business logic, call tools/repos | HTTP request/response objects |
| Tool / utility | Single-purpose transformation or query | Side effects outside its own scope |
| Frontend component | Render UI, emit events | Direct API calls (use hooks/stores), business logic |

### 2.2 No God Files
- A file that does more than one conceptual thing must be split.
- Hard limit: **300 lines per file.** If you are approaching this, flag it and propose a split before continuing.
- One class / one responsibility. One route file / one resource.

### 2.3 Configuration Over Hardcoding
- Zero hardcoded secrets, URLs, model names, port numbers, or file paths in source code.
- All environment-dependent values go in `.env` and are accessed via a single config module (`config.py` / `config.ts`).
- If you write a string that looks like a URL, a key, or a number that could ever change — it belongs in `.env`.

### 2.4 Dependency Direction
Dependencies flow **inward only**:
```
Routes → Services → Tools/Repos → DB/External APIs
```
A lower layer must never import from a higher layer. No circular imports. Ever.

---

## 3. Code Quality Rules

### 3.1 Naming
- **Variables/functions**: `camelCase` (JS/TS), `snake_case` (Python). No abbreviations unless industry-standard (`req`, `res`, `ctx`, `db` are fine; `tmp`, `x`, `data2` are not).
- **Classes/Types/Interfaces**: `PascalCase` always.
- **Constants**: `SCREAMING_SNAKE_CASE`.
- **Booleans**: Must read as a question. `isLoading`, `hasError`, `canUpload`. Never `loading`, `error`, `upload`.
- **Functions**: Must be verbs. `parseChunks()`, `searchClauses()`, `renderMessage()`. Never `chunks()`, `clauses()`, `message()`.
- **Files**: Match their primary export. `SearchClausesTool.ts` exports `SearchClausesTool`. No `utils.py`, `helpers.ts`, `misc.js`.

### 3.2 Function Rules
- **Maximum function length: 40 lines.** If it exceeds this, it is doing more than one thing. Split it.
- **Maximum parameters: 3.** If you need more, use a typed object/dataclass.
- **No nested callbacks or .then().then() chains** — use async/await always.
- **No side effects in pure functions.** A function that transforms data must not also write to a DB or mutate external state.

### 3.3 Error Handling — Mandatory Pattern
Never swallow errors silently. Every try/catch must either:
1. Re-throw with added context, OR
2. Return a structured error object, OR
3. Log the error AND handle the failure gracefully

**Forbidden patterns:**
```python
# NEVER do this
try:
    result = do_thing()
except:
    pass  # silent swallow — this is a bug, not a fix
```

```typescript
// NEVER do this
try {
  const result = await doThing();
} catch (e) {
  console.log(e); // logging without handling is also forbidden
}
```

**Required pattern (Python):**
```python
try:
    result = do_thing()
except SpecificException as e:
    raise ServiceError(f"Failed to do_thing: {e}") from e
```

**Required pattern (TypeScript):**
```typescript
try {
  const result = await doThing();
} catch (error) {
  throw new AppError('doThing failed', { cause: error, context: { ...relevantData } });
}
```

### 3.4 Type Safety
- **TypeScript**: `strict: true` is non-negotiable. Zero use of `any`. If you don't know the type, use `unknown` and narrow it.
- **Python**: All function signatures must have type hints. Return types are mandatory. Use `Optional[X]` not `X | None` for Python < 3.10.
- No implicit returns in typed functions. Every code path must return the declared type.

### 3.5 Comments — The Right Kind Only
Comments explain **why**, never **what**. The code explains what.

```python
# WRONG: explains what (the code already says this)
# Loop through chunks and embed each one
for chunk in chunks:
    embed(chunk)

# RIGHT: explains why (non-obvious business reason)
# Embed sequentially, not in batch — the embedding model has a 512-token context
# limit and batching causes silent truncation without error.
for chunk in chunks:
    embed(chunk)
```

- Every public function/class/endpoint must have a **one-line docstring** stating its contract.
- No commented-out code in commits. Delete it. Git history exists for a reason.

---

## 4. API Design Rules (FastAPI)

### 4.1 Response Shape — Always Consistent
Every endpoint returns a typed Pydantic model. No returning raw dicts.

**Success shape:**
```python
class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Any
    message: Optional[str] = None
```

**Error shape:**
```python
class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: str          # human-readable message
    code: str           # machine-readable code e.g. "FILE_TOO_LARGE"
    details: Optional[dict] = None
```

HTML error pages from FastAPI are forbidden. Add a global exception handler in `main.py`.

### 4.2 HTTP Status Codes — Use Them Correctly
| Situation | Code |
|---|---|
| Created a resource | 201 |
| Async job accepted | 202 |
| Invalid input (client error) | 400 |
| Not found | 404 |
| File too large | 413 |
| Unprocessable entity (valid JSON, wrong shape) | 422 |
| Server error | 500 |

Returning 200 with `{"status": "error"}` in the body is forbidden.

### 4.3 Input Validation
- All request bodies validated via Pydantic before entering any service function.
- File uploads: validate MIME type server-side (not just file extension).
- Never use user-provided strings as filesystem paths. Map to UUID-based temp paths.

### 4.4 SSE Endpoints
- Must emit a `done` event as the final event so the client knows when to close the connection.
- Must emit structured JSON in `data:` field, never raw strings.
- Must handle client disconnection gracefully (catch `asyncio.CancelledError`).

---

## 5. Frontend Rules (Next.js / React)

### 5.1 Component Rules
- One component per file. Filename = component name.
- Components are **dumb by default**: they receive props and render. Logic lives in hooks.
- No business logic inside JSX. Extract to a named function before the return statement.
- Max component length: **120 lines** including imports. If longer, decompose.

### 5.2 Data Fetching
- All API calls live in `/hooks` or `/lib/api`. Never call `fetch()` directly inside a component.
- Use `async/await`. No `.then()` chains in component code.
- Every fetch must handle three states: `loading`, `error`, `success`. No missing states.

### 5.3 State Management
- Local UI state → `useState`
- Shared client state → `useContext` or Zustand (not prop-drilling past 2 levels)
- Server state → React Query or SWR (not `useEffect` + `useState` fetch combos)
- No `useEffect` for data transformation. Derive state with `useMemo` instead.

### 5.4 SSE / Streaming
- Use native `EventSource` API or `fetch` with `ReadableStream`. No third-party SSE libs.
- Parse every `event.data` inside a try/catch. Malformed JSON from the server must not crash the UI.
- Always call `eventSource.close()` in the cleanup function of the effect.
- Show a connection error state if the SSE connection drops unexpectedly.

### 5.5 Styling
- One styling system. Pick Tailwind or CSS Modules — not both in the same project.
- No inline `style={{}}` except for dynamic values that cannot be expressed in class utilities.
- No magic numbers in CSS. Define design tokens for colors, spacing, font sizes.
- All interactive elements must have a visible focus state (accessibility is not optional).

---

## 6. LangGraph / AI Agent Rules

### 6.1 Tools
- Every `@tool` must have a complete docstring that the LLM can read. This IS the tool's API contract.
- Tools must be **pure from the agent's perspective**: same input → deterministic retrieval (no randomness).
- Tools must never access `global` state. Inject dependencies via closure or partial application.
- If a tool fails, it must return a descriptive error string — not raise an exception that crashes the graph.

```python
@tool
def search_legal_clauses(query: str) -> str:
    """
    Search the indexed legal document for clauses relevant to the query.
    Returns the top 3 matching chunks with their page numbers and headings.
    If no results are found, returns a message stating so.
    Never raises exceptions — returns error description as string on failure.
    """
    try:
        results = chroma_collection.query(query_texts=[query], n_results=3)
        if not results["documents"][0]:
            return "No relevant clauses found in the indexed documents."
        return format_results(results)
    except Exception as e:
        return f"Search failed: {e}. Please try a different query."
```

### 6.2 System Prompts
- System prompts live in a dedicated `prompts.py` file. Never inline in the graph definition.
- Anti-hallucination instructions are non-negotiable and must not be weakened by user messages.
- All prompts are versioned with a comment: `# v1.0 — initial grounding prompt`.

### 6.3 Persistence
- `SqliteSaver` must be initialized once at app startup, not per-request.
- `thread_id` must be validated as a UUID before being passed to the graph.
- The checkpointer DB file path comes from `.env`, not hardcoded.

### 6.4 Streaming Events
Emit exactly these event types, nothing else:
```
event: tool_call   data: {"tool": "<name>", "query": "<input>"}
event: token       data: {"text": "<chunk>"}
event: done        data: {"finish_reason": "stop" | "error", "error": null | "<msg>"}
```

---

## 7. Testing Rules

### 7.1 What Must Be Tested (No Exceptions)
- Every service function (unit test, mocked dependencies)
- Every API endpoint (integration test, real HTTP)
- Every LangGraph tool (unit test with mock ChromaDB)
- Every utility/parser function (unit test)

### 7.2 What You Don't Need to Test
- Framework boilerplate (FastAPI routing plumbing, Next.js config)
- Third-party library internals
- UI rendering aesthetics

### 7.3 Test Rules
- Test file lives next to the file it tests: `ingestion.py` → `test_ingestion.py`
- Test function names describe behavior: `test_upload_returns_chunk_count_on_valid_pdf` not `test_upload`
- No `assert True` or empty test bodies as placeholders. Incomplete tests are deleted, not committed.
- Each test has exactly one logical assertion. If you need more, write more tests.

### 7.4 Acceptance Criteria (Replaces e2e tests for now)
The system is shippable only when it passes all 5 demo checks from the interview brief:
1. PDF upload → chunk count returned
2. Query → tool call badge fires → streamed answer with [Page X] citations
3. Out-of-scope question → "This clause is not present in the document."
4. Browser refresh with same thread_id → history restored
5. FastAPI restart → history survives

---

## 8. Git & File Discipline

### 8.1 Never Commit
- `.env` files (only `.env.example` with placeholder values)
- `__pycache__/`, `*.pyc`, `.DS_Store`, `node_modules/`
- SQLite `.db` files (the checkpointer database is runtime state, not source)
- Any file over 5MB

### 8.2 Commit Message Format
```
<type>(<scope>): <what changed in present tense>

type: feat | fix | refactor | test | docs | chore
scope: ingestion | agent | tools | frontend | config | deps

Examples:
feat(ingestion): add heading-aware chunking with page metadata
fix(agent): handle empty ChromaDB collection gracefully
refactor(tools): extract clause formatter to separate utility
```

### 8.3 File Organization — Enforce This Structure
```
/backend
  main.py           ← FastAPI app init, CORS, global error handler only
  config.py         ← All env var loading. Single source of truth.
  ingestion.py      ← PDF parsing, chunking, embedding, ChromaDB upsert
  agent.py          ← LangGraph graph definition, node wiring
  tools.py          ← All @tool functions
  prompts.py        ← All system prompts as string constants
  checkpointer.py   ← SqliteSaver init and thread management
  models.py         ← All Pydantic request/response models
  /tests
    test_ingestion.py
    test_tools.py
    test_agent.py

/frontend
  /app
    /api            ← Next.js route handlers (thin, delegate to /lib)
    /chat           ← Chat page
    layout.tsx
    page.tsx
  /components       ← Pure UI components (dumb, props-only)
  /hooks            ← All data fetching and stateful logic
  /lib
    api.ts          ← All fetch calls in one place
    sse.ts          ← SSE connection logic
    types.ts        ← Shared TypeScript types
  /stores           ← Zustand stores if needed
```

---

## 9. Forbidden Patterns — Instant Red Flags

If you find yourself writing any of the following, stop and redesign:

| Pattern | Why It's Forbidden | Fix |
|---|---|---|
| `except: pass` | Silently hides bugs | Re-throw or handle explicitly |
| `any` in TypeScript | Defeats type safety | Use `unknown` and narrow |
| `console.log` left in committed code | Not observability | Use a logger or remove |
| Fetching in a component body | Unmaintainable | Move to a custom hook |
| Hardcoded localhost URLs | Breaks in prod | Use env config |
| `// TODO` without a ticket/issue reference | Promises that won't be kept | Fix it now or delete it |
| Global mutable state | Race conditions, untestable | Dependency injection |
| Copying code instead of importing | Divergence bugs | Extract to shared module |
| `!` non-null assertion in TypeScript | Lying to the compiler | Handle the null case |
| `.env` committed to git | Security incident | Remove, rotate secrets, add to .gitignore |

---

## 10. When You Are Stuck

Do not generate speculative code hoping it works. Instead:

1. **State what you know** about the problem.
2. **State what you don't know** (the specific blocker).
3. **Propose two approaches** with tradeoffs.
4. **Ask which to proceed with.**

Generating broken code and then fixing it in the next message wastes context and creates confusion. One correct pass beats three sloppy passes.

---

## Acknowledgment Protocol

When starting any task in this project, your first message must begin with:

> "QUALITY.md read. Task: [one sentence]. Governed by: [rule numbers]. Proceeding."

If you cannot identify which rules govern the task, state that before proceeding.