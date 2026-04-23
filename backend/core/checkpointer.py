"""Conversation persistence using AsyncSqliteSaver."""
from typing import Optional

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from core.config import config

_checkpointer: Optional[AsyncSqliteSaver] = None


def get_checkpointer() -> Optional[AsyncSqliteSaver]:
    """Return the singleton checkpointer instance set during startup."""
    return _checkpointer


def set_checkpointer(checkpointer: AsyncSqliteSaver) -> None:
    """Store the checkpointer instance created during app lifespan."""
    global _checkpointer
    _checkpointer = checkpointer
