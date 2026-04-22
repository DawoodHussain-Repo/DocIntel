"""Conversation persistence using AsyncSqliteSaver."""
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from backend.config import config


async def get_checkpointer():
    """Initialize and return AsyncSqliteSaver for conversation persistence.
    
    Returns:
        AsyncSqliteSaver: Configured checkpointer instance
    """
    checkpointer = AsyncSqliteSaver.from_conn_string(config.SQLITE_DB_PATH)
    await checkpointer.setup()
    return checkpointer
