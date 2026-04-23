# DocIntel - Production Architecture

This document describes the production-grade architecture of DocIntel, focusing on the LangGraph agent implementation.

---

## Core Principles

### 1. Separation of Concerns

```
HTTP Layer (FastAPI)
    ↓
Service Layer (AgentService)
    ↓
Graph Layer (LangGraph)
    ↓
Node Layer (Pure Functions)
    ↓
External Dependencies (LLM, Tools, DB)
```

**Never mix these layers.** Each has a single responsibility.

### 2. Explicit State Management

State is a **TypedDict** with required fields:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    run_id: str
    thread_id: str
    next_step: str
    error: str | None
```

**No optional fields.** No random dicts. State is a contract.

### 3. Dependency Injection

```python
# Bad: Global state
llm = ChatOpenAI(...)

# Good: Dependency injection
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(...)

@app.get("/chat")
def chat(llm: ChatOpenAI = Depends(get_llm)):
    ...
```

Benefits:
- Testable (mock dependencies)
- Swappable (change LLM provider)
- Cacheable (singleton pattern)

### 4. Pure Node Functions

```python
# Bad: Side effects everywhere
def node(state):
    db.save(state)  # Side effect
    logger.info("...")  # Side effect
    return state

# Good: Pure function
def node(state: AgentState) -> dict:
    result = process(state)
    return {"key": result}  # Only returns state update
```

Logging is acceptable (observability), but no DB writes, no global mutations.

---

## Directory Structure

```
backend/
├── agents/                    # LangGraph agent definitions
│   ├── state.py               # State schema (TypedDict)
│   ├── graph.py               # Graph construction
│   └── nodes/                 # Node functions
│       ├── llm_node.py        # LLM invocation
│       └── tool_node.py       # Tool execution
├── dependencies/              # FastAPI dependencies
│   ├── llm.py                 # LLM singleton
│   └── agent.py               # Agent service factory
├── services/                  # Service layer
│   ├── agent_service.py       # Graph execution wrapper
│   ├── chat_service.py        # SSE streaming
│   └── upload_service.py      # Upload processing
├── core/                      # Core business logic
│   ├── config.py              # Configuration
│   ├── models.py              # Pydantic schemas
│   ├── tools.py               # LangChain tools
│   ├── prompts.py             # System prompts
│   └── ...
├── api/                       # API layer
│   └── middleware.py          # Request tracing
├── utils/                     # Utilities
│   └── logger.py              # Structured logging
└── main.py                    # FastAPI app
```

---

## Agent Architecture

### Graph Structure

```
START
  ↓
llm_node (LLM invocation)
  ↓
should_continue (routing)
  ├─→ tools → llm_node (loop)
  └─→ END
```

### State Flow

```
Initial State:
{
  "messages": [HumanMessage("query")],
  "run_id": "uuid",
  "thread_id": "uuid",
  "next_step": "llm",
  "error": None
}

After LLM:
{
  "messages": [..., AIMessage(tool_calls=[...])],
  "next_step": "tools",  # or "end"
  "error": None
}

After Tools:
{
  "messages": [..., ToolMessage(...)],
  "next_step": "llm",
  "error": None
}

Final State:
{
  "messages": [..., AIMessage("answer")],
  "next_step": "end",
  "error": None
}
```

### Node Responsibilities

| Node | Responsibility | Returns |
|------|---------------|---------|
| `llm_node` | Invoke LLM with retry | `{"messages": [...], "next_step": "tools" or "end"}` |
| `tool_node` | Execute tools with retry | `{"messages": [...], "next_step": "llm"}` |
| `should_continue` | Route based on next_step | `"tools"`, `"llm"`, or `END` |

---

## Dependency Injection Flow

```
Request
  ↓
FastAPI Route
  ↓
get_agent_service(chroma_client)
  ↓
get_agent_graph(chroma_client)
  ├─→ get_llm() [cached]
  ├─→ create_tools(chroma_client)
  └─→ build_graph(llm, tools)
  ↓
AgentService(graph)
  ↓
agent_service.stream(query, thread_id)
  ↓
Response
```

**Key Points:**
- LLM is cached (singleton)
- Graph is cached (singleton)
- Agent service is created per-request
- ChromaDB client is passed from app.state

---

## Retry Logic

### LLM Invocation

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def _invoke_llm_with_retry(llm, messages):
    return await llm.ainvoke(messages)
```

**Behavior:**
- Attempt 1: Immediate
- Attempt 2: Wait 2s
- Attempt 3: Wait 4s
- Fail: Raise exception

### Tool Execution

```python
@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
)
async def _execute_with_retry(state):
    return await self.tool_node.ainvoke(state)
```

**Behavior:**
- Attempt 1: Immediate
- Attempt 2: Wait 1s
- Fail: Raise exception

---

## Error Handling

### Node-Level Errors

```python
try:
    result = await llm.ainvoke(messages)
    return {"messages": [result], "next_step": "tools"}
except Exception as error:
    logger.exception("llm_invocation_failed")
    return {"next_step": "end", "error": str(error)}
```

**Never let exceptions bubble up.** Catch, log, and return error state.

### Service-Level Errors

```python
try:
    async for event in agent_service.stream(...):
        yield event
except Exception as error:
    logger.exception("agent_stream_failed")
    yield error_event
```

**Always yield a done event**, even on failure.

---

## Observability

### Structured Logging

Every node logs:
- Entry: `node_enter` with input summary
- Exit: `node_exit` with duration and output keys
- Error: `node_error` with exception details

Example:
```json
{
  "event": "node_enter",
  "node": "llm_node",
  "run_id": "abc-123",
  "thread_id": "def-456",
  "message_count": 3,
  "timestamp": "2026-04-23T10:00:00Z"
}
```

### Context Propagation

```python
structlog.contextvars.bind_contextvars(
    run_id=run_id,
    thread_id=thread_id,
)
```

**All logs in the request** automatically include `run_id` and `thread_id`.

---

## Persistence

### Conversation Memory

```python
checkpointer = AsyncSqliteSaver.from_conn_string("./memory.db")
graph = workflow.compile(checkpointer=checkpointer)
```

**State is automatically persisted** after each node execution.

### Retrieval

```python
config = {"configurable": {"thread_id": thread_id}}
state = await graph.ainvoke(input, config)
```

**Previous messages are automatically loaded** from checkpointer.

---

## Streaming

### Service Layer

```python
async def stream(self, user_input, thread_id, run_id):
    initial_state = self._create_initial_state(...)
    config = {"configurable": {"thread_id": thread_id}}
    
    async for event in self.graph.astream_events(initial_state, config):
        yield event
```

### HTTP Layer

```python
async def chat_stream(query, thread_id):
    agent_service = get_agent_service(...)
    event_stream = stream_chat_events(agent_service, query, thread_id)
    return StreamingResponse(event_stream, media_type="text/event-stream")
```

**Service layer yields events, HTTP layer wraps in SSE.**

---

## Testing Strategy

### Unit Tests (Nodes)

```python
def test_llm_node():
    state = {"messages": [...], "run_id": "test", ...}
    llm = MockLLM()
    result = await llm_node(state, llm)
    assert result["next_step"] == "tools"
```

**Test nodes in isolation** with mock dependencies.

### Integration Tests (Graph)

```python
def test_graph_execution():
    graph = build_graph(mock_llm, mock_tools)
    state = {"messages": [...], ...}
    result = await graph.ainvoke(state)
    assert result["error"] is None
```

**Test graph with mock LLM and tools.**

### E2E Tests (Service)

```python
def test_agent_service():
    service = AgentService(real_graph)
    result = await service.run("query", "thread-123")
    assert len(result["messages"]) > 1
```

**Test service with real graph, mock external dependencies.**

---

## Scaling Considerations

### Horizontal Scaling

- **Stateless routes**: Each request is independent
- **Shared persistence**: SQLite checkpointer on network storage
- **Sticky sessions**: For SSE streaming

### Vertical Scaling

- **LLM caching**: Singleton pattern reduces memory
- **Connection pooling**: ChromaDB client reuse
- **Async execution**: Non-blocking I/O

### Background Processing

For long-running tasks:
```python
from celery import Celery

@celery.task
def process_document(file_path):
    agent_service = get_agent_service()
    result = agent_service.run(...)
    return result
```

---

## Common Pitfalls

| ❌ Anti-pattern | ✅ Correct |
|----------------|-----------|
| Logic in routes | Logic in services/nodes |
| Global LLM instance | Dependency injection |
| Optional state fields | Required fields with defaults |
| Mega-node functions | Small, focused nodes |
| No retry logic | Retry with exponential backoff |
| Silent failures | Log and return error state |
| Blocking I/O | Async/await everywhere |

---

## Migration Guide

### From Old Architecture

**Before:**
```python
async def create_agent(chroma_client):
    llm = get_llm()
    tools = [...]
    
    async def call_model(state):
        ...
    
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    return workflow.compile()
```

**After:**
```python
# dependencies/llm.py
@lru_cache
def get_llm():
    return ChatOpenAI(...)

# agents/nodes/llm_node.py
async def llm_node(state, llm):
    ...

# agents/graph.py
def build_graph(llm, tools):
    workflow = StateGraph(AgentState)
    workflow.add_node("llm", lambda s: llm_node(s, llm))
    return workflow.compile()

# dependencies/agent.py
def get_agent_service(chroma_client):
    llm = get_llm()
    tools = create_tools(chroma_client)
    graph = build_graph(llm, tools)
    return AgentService(graph)
```

---

## Next Steps

1. **Add more nodes**: Planner, validator, finalizer
2. **Add human-in-the-loop**: `interrupt_before=["tools"]`
3. **Add max steps guard**: Prevent infinite loops
4. **Add streaming progress**: Yield node transitions
5. **Add metrics**: Track latency, token usage, errors

---

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Tenacity Retry](https://tenacity.readthedocs.io/)
- [Structlog](https://www.structlog.org/)
