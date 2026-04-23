"""LLM invocation node for agent graph."""
import structlog
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.state import AgentState
from core.prompts import SYSTEM_PROMPT


logger = structlog.get_logger("docintel.agents.nodes.llm")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _invoke_llm_with_retry(llm: ChatOpenAI, messages: list) -> any:
    """Invoke LLM with exponential backoff retry."""
    return await llm.ainvoke(messages)


async def llm_node(state: AgentState, llm: ChatOpenAI) -> dict:
    """
    Call LLM with system prompt and conversation history.
    
    This is a pure function that:
    1. Adds system prompt if not present
    2. Invokes LLM with retry logic
    3. Returns updated state with LLM response
    
    Args:
        state: Current agent state
        llm: Configured LLM instance
        
    Returns:
        Updated state dict with new message
    """
    run_id = state.get("run_id", "unknown")
    thread_id = state.get("thread_id", "unknown")
    
    node_logger = logger.bind(
        node="llm_node",
        run_id=run_id,
        thread_id=thread_id,
    )
    
    node_logger.info("llm_invocation_started", message_count=len(state["messages"]))
    
    try:
        messages = state["messages"]
        
        # Add system prompt if not present
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        # Invoke LLM with retry
        response = await _invoke_llm_with_retry(llm, messages)
        
        # Check if LLM wants to call tools
        has_tool_calls = bool(getattr(response, "tool_calls", None))
        next_step = "tools" if has_tool_calls else "end"
        
        node_logger.info(
            "llm_invocation_completed",
            has_tool_calls=has_tool_calls,
            next_step=next_step,
        )
        
        return {
            "messages": [response],
            "next_step": next_step,
            "error": None,
        }
        
    except Exception as error:
        node_logger.exception(
            "llm_invocation_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return {
            "next_step": "end",
            "error": f"LLM invocation failed: {error}",
        }
