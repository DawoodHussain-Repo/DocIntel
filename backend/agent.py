import os
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from backend.tools import search_legal_clauses
from backend.checkpointer import get_checkpointer
from dotenv import load_dotenv

load_dotenv()

# System prompt
SYSTEM_PROMPT = """You are DocIntel, an AI assistant specialized in analyzing legal contracts.
Rules you MUST follow:
- You ONLY use information returned by the search_legal_clauses tool. Never use prior knowledge.
- Every factual claim must reference the clause it came from. Append [Page X] to each cited sentence.
- If the user asks about something not present in the document, respond: 'This clause is not present in the document.'
- Do not guess, infer, or hallucinate contract terms."""

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def get_llm():
    """Initialize LLM based on provider selection."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if provider == "groq":
        return ChatOpenAI(
            model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            streaming=True,
            temperature=0.7
        )
    elif provider == "lmstudio":
        return ChatOpenAI(
            model=os.getenv("LMSTUDIO_MODEL", "local-model"),
            api_key="lm-studio",  # LM Studio accepts any string
            base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            streaming=True,
            temperature=0.7
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Use 'groq' or 'lmstudio'")

def create_agent():
    """Create the LangGraph agent with tools and checkpointer."""
    
    # Initialize LLM based on provider
    llm = get_llm()
    
    # Bind tools to LLM
    tools = [search_legal_clauses]
    llm_with_tools = llm.bind_tools(tools)
    
    # Define agent node
    def call_model(state: AgentState):
        messages = state["messages"]
        
        # Inject system prompt if not present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Define routing logic
    def should_continue(state: AgentState):
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
    checkpointer = get_checkpointer()
    app = workflow.compile(checkpointer=checkpointer)
    
    return app
