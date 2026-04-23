"""LangGraph agent implementation with tools and checkpointer."""
from typing import Annotated, Any, TypedDict

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from checkpointer import get_checkpointer
from config import config
from prompts import SYSTEM_PROMPT
from tools import create_search_legal_clauses_tool


class AgentState(TypedDict):
    """State schema for the DocIntel conversation graph."""

    messages: Annotated[list, add_messages]


def get_llm() -> ChatOpenAI:
    """Build a configured chat model instance for the selected provider."""
    if config.LLM_PROVIDER == "groq":
        return ChatOpenAI(
            model=config.GROQ_MODEL,
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
            streaming=True,
            temperature=config.LLM_TEMPERATURE,
        )

    if config.LLM_PROVIDER == "lmstudio":
        return ChatOpenAI(
            model=config.LMSTUDIO_MODEL,
            api_key=config.LMSTUDIO_API_KEY,
            base_url=config.LMSTUDIO_BASE_URL,
            streaming=True,
            temperature=config.LLM_TEMPERATURE,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER}. Use 'groq' or 'lmstudio'."
    )


async def create_agent(chroma_client: Any) -> Any:
    """Create and compile the LangGraph app with persistence and tools."""
    llm = get_llm()
    search_legal_clauses = create_search_legal_clauses_tool(chroma_client)
    tools = [search_legal_clauses]

    llm_with_tools = llm.bind_tools(tools)

    async def call_model(state: AgentState) -> dict:
        """Call the model node with system prompt grounding and tool binding."""
        messages = state["messages"]
        if not any(isinstance(message, SystemMessage) for message in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """Route model output to tools when tool calls are requested."""
        last_message = state["messages"][-1]
        if getattr(last_message, "tool_calls", None):
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
    return workflow.compile(checkpointer=checkpointer)
