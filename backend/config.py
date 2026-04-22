"""Configuration module - single source of truth for all environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""
    
    # LLM Provider Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    
    # LM Studio Configuration
    LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "local-model")
    LMSTUDIO_API_KEY = "lm-studio"  # LM Studio accepts any string
    
    # Storage Configuration
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./docintel_memory.db")
    
    # Server Configuration
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = 20
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_MIME_TYPES = ["application/pdf"]
    
    @classmethod
    def validate(cls):
        """Validate required configuration is present."""
        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        
        if cls.LLM_PROVIDER not in ["groq", "lmstudio"]:
            raise ValueError(f"Invalid LLM_PROVIDER: {cls.LLM_PROVIDER}. Must be 'groq' or 'lmstudio'")

config = Config()
