"""Agent state schema for DocIntel legal document intelligence."""
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State schema for the DocIntel conversation graph.
    
    All fields are required to ensure proper state tracking.
    """
    
    messages: Annotated[list, add_messages]
    """Conversation messages with automatic message list merging."""
    
    run_id: str
    """Unique identifier for this agent execution run."""
    
    thread_id: str
    """Thread identifier for conversation persistence."""
    
    next_step: str
    """Next action to take (for conditional routing)."""
    
    error: str | None
    """Error message if execution failed."""
