"""LangGraph agent implementation with tools and checkpointer."""
import time
from functools import wraps
from typing import Annotated, Any, Callable, TypedDict

import structlog
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from checkpointer import get_checkpointer
from config import config
from prompts import SYSTEM_PROMPT
from tools import create_search_legal_clauses_tool


logger = structlog.get_logger("docintel.agent")


class AgentState(TypedDict):
    """State schema for the DocIntel conversation graph."""

    messages: Annotated[list, add_messages]
    run_id: str | None
    thread_id: str | None


def log_node(node_name: str) -> Callable:
    """Decorator that wraps LangGraph nodes with entry/exit logging and timing."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def async_wrapper(state: AgentState) -> dict:
            run_id = state.get("run_id", "unknown")
            thread_id = state.get("thread_id", "unknown")
            
            node_logger = logger.bind(
                node=node_name,
                run_id=run_id,
                thread_id=thread_id,
            )
            
            start_time = time.perf_counter()
            node_logger.info("node_enter", message_count=len(state.get("messages", [])))
            
            try:
                result = await fn(state)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                
                output_keys = list(result.keys()) if result else []
                node_logger.info(
                    "node_exit",
                    output_keys=output_keys,
                    duration_ms=duration_ms,
                )
                return result
                
            except Exception as error:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                node_logger.exception(
                    "node_error",
                    error_type=type(error).__name__,
                    error_message=str(error),
                    duration_ms=duration_ms,
                )
                raise
        
        @wraps(fn)
        def sync_wrapper(state: AgentState) -> dict:
            run_id = state.get("run_id", "unknown")
            thread_id = state.get("thread_id", "unknown")
            
            node_logger = logger.bind(
                node=node_name,
                run_id=run_id,
                thread_id=thread_id,
            )
            
            start_time = time.perf_counter()
            node_logger.info("node_enter", message_count=len(state.get("messages", [])))
            
            try:
                result = fn(state)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                
                output_keys = list(result.keys()) if result else []
                node_logger.info(
                    "node_exit",
                    output_keys=output_keys,
                    duration_ms=duration_ms,
                )
                return result
                
            except Exception as error:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                node_logger.exception(
                    "node_error",
                    error_type=type(error).__name__,
                    error_message=str(error),
                    duration_ms=duration_ms,
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def get_llm() -> ChatOpenAI:
    """Build a configured chat model instance for the selected provider."""
    if config.LLM_PROVIDER == "groq":
        return ChatOpenAI(
            model=config.GROQ_MODEL,
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
            streaming=True,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=2048,
        )

    if config.LLM_PROVIDER == "lmstudio":
        return ChatOpenAI(
            model=config.LMSTUDIO_MODEL,
            api_key=config.LMSTUDIO_API_KEY,
            base_url=config.LMSTUDIO_BASE_URL,
            streaming=True,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=2048,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER}. Use 'groq' or 'lmstudio'."
    )


async def create_agent(chroma_client: Any) -> Any:
    """Create and compile the LangGraph app with persistence and tools."""
    logger.info("agent_initialization_started", provider=config.LLM_PROVIDER)
    
    llm = get_llm()
    search_legal_clauses = create_search_legal_clauses_tool(chroma_client)
    tools = [search_legal_clauses]

    llm_with_tools = llm.bind_tools(tools)

    @log_node("call_model")
    async def call_model(state: AgentState) -> dict:
        """Call the model node with system prompt grounding and tool binding."""
        messages = state["messages"]
        if not any(isinstance(message, SystemMessage) for message in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    @log_node("should_continue")
    def should_continue(state: AgentState) -> str:
        """Route model output to tools when tool calls are requested."""
        last_message = state["messages"][-1]
        has_tool_calls = bool(getattr(last_message, "tool_calls", None))
        
        logger.info(
            "routing_decision",
            has_tool_calls=has_tool_calls,
            next_node="tools" if has_tool_calls else "END",
        )
        
        if has_tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    workflow.add_edge("tools", "agent")

    checkpointer = get_checkpointer()
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    
    logger.info(
        "agent_initialization_completed",
        nodes=["agent", "tools"],
        has_checkpointer=checkpointer is not None,
    )
    
    return compiled_graph
