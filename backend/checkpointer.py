import os
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from dotenv import load_dotenv

load_dotenv()

async def get_checkpointer():
    """Initialize and return AsyncSqliteSaver for conversation persistence."""
    db_path = os.getenv("SQLITE_DB_PATH", "./docintel_memory.db")
    checkpointer = AsyncSqliteSaver.from_conn_string(db_path)
    await checkpointer.setup()
    return checkpointer
