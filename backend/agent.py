"""LangGraph agent implementation with tools and checkpointer."""
import os
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from backend.tools import search_legal_clauses
from backend.prompts import SYSTEM_PROMPT
from backend.config import config


class AgentState(TypedDict):
    """State schema for the agent graph."""
    messages: Annotated[list, add_messages]


def get_llm():
    """Initialize LLM based on provider selection from config.
    
    Returns:
        ChatOpenAI: Configured LLM instance
        
    Raises:
        ValueError: If LLM_PROVIDER is invalid
    """
    if config.LLM_PROVIDER == "groq":
        return ChatOpenAI(
            model=config.GROQ_MODEL,
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
            streaming=True,
            temperature=0.7
        )
    elif config.LLM_PROVIDER == "lmstudio":
        return ChatOpenAI(
            model=config.LMSTUDIO_MODEL,
            api_key=config.LMSTUDIO_API_KEY,
            base_url=config.LMSTUDIO_BASE_URL,
            streaming=True,
            temperature=0.7
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER}. Use 'groq' or 'lmstudio'")


async def create_agent():
    """Create the LangGraph agent with tools and checkpointer.
    
    Returns:
        Compiled LangGraph application with persistence
    """
    from backend.checkpointer import get_checkpointer
    
    # Initialize LLM based on provider
    llm = get_llm()
    
    # Bind tools to LLM
    tools = [search_legal_clauses]
    llm_with_tools = llm.bind_tools(tools)
    
    # Define agent node
    def call_model(state: AgentState):
        """Agent node that calls the LLM with tools."""
        messages = state["messages"]
        
        # Inject system prompt if not present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Define routing logic
    def should_continue(state: AgentState):
        """Determine if we should continue to tools or end."""
        last_message = state["messages"][-1]
        
        # If there are tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # Otherwise, end
        return END
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    # Compile with checkpointer
    checkpointer = await get_checkpointer()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app
