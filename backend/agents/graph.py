"""LangGraph graph construction for DocIntel agent."""
from typing import Any

import structlog
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from agents.nodes.llm_node import llm_node
from agents.nodes.tool_node import ToolExecutionNode
from agents.state import AgentState
from core.checkpointer import get_checkpointer


logger = structlog.get_logger("docintel.agents.graph")


def should_continue(state: AgentState) -> str:
    """
    Routing function to determine next node.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name: "tools", "llm", or END
    """
    next_step = state.get("next_step", "end")
    error = state.get("error")
    
    # If there's an error, end execution
    if error:
        logger.warning("routing_to_end_due_to_error", error=error)
        return END
    
    # Route based on next_step
    if next_step == "tools":
        return "tools"
    elif next_step == "llm":
        return "llm"
    else:
        return END


def build_graph(llm: ChatOpenAI, tools: list, chroma_client: Any = None) -> Any:
    """
    Build and compile the LangGraph agent.
    
    Graph structure:
        START → llm → [tools → llm]* → END
    
    Args:
        llm: Configured LLM instance
        tools: List of available tools
        chroma_client: ChromaDB client (optional, for tool initialization)
        
    Returns:
        Compiled LangGraph instance
    """
    logger.info("graph_build_started", tool_count=len(tools))
    
    # Create tool execution node
    tool_executor = ToolExecutionNode(tools)
    
    # Create workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("llm", lambda state: llm_node(state, llm))
    workflow.add_node("tools", tool_executor)
    
    # Set entry point
    workflow.set_entry_point("llm")
    
    # Add conditional edges from LLM
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    
    # Add edge from tools back to LLM
    workflow.add_conditional_edges(
        "tools",
        should_continue,
        {
            "llm": "llm",
            END: END,
        },
    )
    
    # Get checkpointer for persistence
    checkpointer = get_checkpointer()
    
    # Compile with guardrails
    compiled_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],  # No human-in-the-loop for now
        interrupt_after=[],
    )
    
    logger.info(
        "graph_build_completed",
        nodes=["llm", "tools"],
        has_checkpointer=checkpointer is not None,
    )
    
    return compiled_graph
