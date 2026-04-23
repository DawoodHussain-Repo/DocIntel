"""Agent service layer for graph execution."""
import uuid
from typing import Any, AsyncGenerator

import structlog
from langchain_core.messages import HumanMessage

from agents.state import AgentState
from core.config import config


logger = structlog.get_logger("docintel.services.agent")


class AgentService:
    """
    Service layer for LangGraph agent execution.
    
    This wraps the graph and provides:
    - Initial state construction
    - Execution orchestration
    - Streaming support
    - Error handling
    """
    
    def __init__(self, graph: Any):
        """
        Initialize agent service with compiled graph.
        
        Args:
            graph: Compiled LangGraph instance
        """
        self.graph = graph
    
    def _create_initial_state(
        self,
        user_input: str,
        thread_id: str,
        run_id: str | None = None,
    ) -> AgentState:
        """
        Create initial state for graph execution.
        
        Args:
            user_input: User's query
            thread_id: Thread identifier for persistence
            run_id: Optional run identifier (generated if not provided)
            
        Returns:
            Initial AgentState
        """
        if not run_id:
            run_id = str(uuid.uuid4())
        
        return AgentState(
            messages=[HumanMessage(content=user_input)],
            run_id=run_id,
            thread_id=thread_id,
            next_step="llm",
            error=None,
        )
    
    async def run(
        self,
        user_input: str,
        thread_id: str,
        run_id: str | None = None,
    ) -> AgentState:
        """
        Execute agent synchronously and return final state.
        
        Args:
            user_input: User's query
            thread_id: Thread identifier
            run_id: Optional run identifier
            
        Returns:
            Final agent state
        """
        initial_state = self._create_initial_state(user_input, thread_id, run_id)
        config_dict = {"configurable": {"thread_id": thread_id}}
        
        logger.info(
            "agent_execution_started",
            run_id=initial_state["run_id"],
            thread_id=thread_id,
        )
        
        try:
            final_state = await self.graph.ainvoke(initial_state, config_dict)
            
            logger.info(
                "agent_execution_completed",
                run_id=initial_state["run_id"],
                message_count=len(final_state.get("messages", [])),
            )
            
            return final_state
            
        except Exception as error:
            logger.exception(
                "agent_execution_failed",
                run_id=initial_state["run_id"],
                error_type=type(error).__name__,
                error_message=str(error),
            )
            raise
    
    async def stream(
        self,
        user_input: str,
        thread_id: str,
        run_id: str | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Execute agent with streaming and yield events.
        
        Args:
            user_input: User's query
            thread_id: Thread identifier
            run_id: Optional run identifier
            
        Yields:
            State updates and events from graph execution
        """
        initial_state = self._create_initial_state(user_input, thread_id, run_id)
        config_dict = {"configurable": {"thread_id": thread_id}}
        
        logger.info(
            "agent_stream_started",
            run_id=initial_state["run_id"],
            thread_id=thread_id,
        )
        
        try:
            async for event in self.graph.astream_events(
                initial_state,
                config_dict,
                version="v1",
            ):
                yield event
            
            logger.info(
                "agent_stream_completed",
                run_id=initial_state["run_id"],
            )
            
        except Exception as error:
            logger.exception(
                "agent_stream_failed",
                run_id=initial_state["run_id"],
                error_type=type(error).__name__,
                error_message=str(error),
            )
            raise
