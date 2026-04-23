"""Tool execution node for agent graph."""
import structlog
from langgraph.prebuilt import ToolNode as LangGraphToolNode
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.state import AgentState


logger = structlog.get_logger("docintel.agents.nodes.tool")


class ToolExecutionNode:
    """
    Wrapper around LangGraph ToolNode with retry logic and logging.
    
    This provides:
    - Automatic retry on tool failures
    - Structured logging
    - Error handling
    """
    
    def __init__(self, tools: list):
        """
        Initialize tool node with available tools.
        
        Args:
            tools: List of LangChain tools
        """
        self.tool_node = LangGraphToolNode(tools)
        self.tools = tools
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def _execute_with_retry(self, state: AgentState) -> dict:
        """Execute tools with retry logic."""
        return await self.tool_node.ainvoke(state)
    
    async def __call__(self, state: AgentState) -> dict:
        """
        Execute tools requested by LLM.
        
        Args:
            state: Current agent state with tool calls
            
        Returns:
            Updated state with tool results
        """
        run_id = state.get("run_id", "unknown")
        thread_id = state.get("thread_id", "unknown")
        
        node_logger = logger.bind(
            node="tool_node",
            run_id=run_id,
            thread_id=thread_id,
        )
        
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        
        node_logger.info(
            "tool_execution_started",
            tool_count=len(tool_calls),
            tools=[tc.get("name", "unknown") for tc in tool_calls],
        )
        
        try:
            result = await self._execute_with_retry(state)
            
            node_logger.info("tool_execution_completed")
            
            return {
                **result,
                "next_step": "llm",  # Always return to LLM after tools
                "error": None,
            }
            
        except Exception as error:
            node_logger.exception(
                "tool_execution_failed",
                error_type=type(error).__name__,
                error_message=str(error),
            )
            return {
                "next_step": "end",
                "error": f"Tool execution failed: {error}",
            }
