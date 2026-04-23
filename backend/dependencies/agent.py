"""Agent dependency injection for FastAPI."""
from functools import lru_cache
from typing import Any

import structlog

from agents.graph import build_graph
from core.tools import create_search_legal_clauses_tool
from dependencies.llm import get_llm
from services.agent_service import AgentService


logger = structlog.get_logger("docintel.dependencies.agent")


@lru_cache(maxsize=1)
def get_agent_graph(chroma_client: Any = None) -> Any:
    """
    Get compiled agent graph (cached singleton).
    
    Args:
        chroma_client: ChromaDB client for tool initialization
        
    Returns:
        Compiled LangGraph instance
    """
    logger.info("agent_graph_initialization_started")
    
    # Get LLM
    llm = get_llm()
    
    # Bind tools to LLM
    if chroma_client:
        search_tool = create_search_legal_clauses_tool(chroma_client)
        tools = [search_tool]
        llm_with_tools = llm.bind_tools(tools)
    else:
        tools = []
        llm_with_tools = llm
    
    # Build graph
    graph = build_graph(llm_with_tools, tools, chroma_client)
    
    logger.info("agent_graph_initialized", tool_count=len(tools))
    
    return graph


def get_agent_service(chroma_client: Any = None) -> AgentService:
    """
    Get agent service instance.
    
    This is the main dependency for routes that need agent execution.
    
    Args:
        chroma_client: ChromaDB client for tool initialization
        
    Returns:
        AgentService instance
    """
    graph = get_agent_graph(chroma_client)
    return AgentService(graph)
