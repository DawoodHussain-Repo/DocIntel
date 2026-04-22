import os
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv

load_dotenv()

def get_checkpointer():
    """Initialize and return SqliteSaver for conversation persistence."""
    db_path = os.getenv("SQLITE_DB_PATH", "./docintel_memory.db")
    return SqliteSaver.from_conn_string(db_path)
