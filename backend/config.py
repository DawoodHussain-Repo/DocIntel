"""Configuration module - single source of truth for all environment variables."""
import os
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parent


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.APP_NAME = os.getenv("APP_NAME", "DocIntel API")
        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
        self.GROQ_BASE_URL = os.getenv(
            "GROQ_BASE_URL",
            "https://api.groq.com/openai/v1",
        )

        self.LMSTUDIO_BASE_URL = os.getenv(
            "LMSTUDIO_BASE_URL",
            "http://localhost:1234/v1",
        )
        self.LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "local-model")
        self.LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lm-studio")

        self.EMBEDDING_MODEL_NAME = os.getenv(
            "EMBEDDING_MODEL_NAME",
            "all-MiniLM-L6-v2",
        )
        self.SEARCH_RESULT_LIMIT = int(os.getenv("SEARCH_RESULT_LIMIT", "3"))

        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
        self.CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

        self.CHROMA_PERSIST_DIR = self._resolve_path(
            os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        )
        self.SQLITE_DB_PATH = self._resolve_path(
            os.getenv("SQLITE_DB_PATH", "./docintel_memory.db")
        )
        self.WORKSPACE_DIR = self._resolve_path(
            os.getenv("WORKSPACE_DIR", "./workspace")
        )

        self.BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

        self.CORS_ORIGINS = self._split_csv_env(
            os.getenv("CORS_ORIGINS", "http://localhost:3000")
        )
        self.ALLOWED_HOSTS = self._split_csv_env(
            os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
        )

        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
        self.MAX_FILE_SIZE_BYTES = self.MAX_FILE_SIZE_MB * 1024 * 1024
        self.MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "2000"))
        self.ALLOWED_MIME_TYPES = ["application/pdf"]

        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()

        self.AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "120"))

    @staticmethod
    def _split_csv_env(raw_value: str) -> List[str]:
        """Parse comma-separated env values into a normalized string list."""
        return [value.strip() for value in raw_value.split(",") if value.strip()]

    @staticmethod
    def _resolve_path(raw_path: str) -> Path:
        """Resolve relative paths against the backend root."""
        path_value = Path(raw_path)
        if path_value.is_absolute():
            return path_value
        return (BACKEND_ROOT / path_value).resolve()

    @staticmethod
    def create_uuid() -> str:
        """Create a UUID string for temporary resource naming."""
        return str(uuid.uuid4())

    def validate(self) -> None:
        """Validate required configuration and safe value ranges."""
        if self.LLM_PROVIDER not in ["groq", "lmstudio"]:
            raise ValueError(
                f"Invalid LLM_PROVIDER: {self.LLM_PROVIDER}. Must be 'groq' or 'lmstudio'."
            )

        if self.LLM_PROVIDER == "groq" and not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")

        if self.MAX_FILE_SIZE_MB <= 0:
            raise ValueError("MAX_FILE_SIZE_MB must be greater than 0")

        if self.MAX_QUERY_LENGTH < 64:
            raise ValueError("MAX_QUERY_LENGTH must be at least 64 characters")

        if not (0 <= self.LLM_TEMPERATURE <= 1):
            raise ValueError("LLM_TEMPERATURE must be between 0 and 1")

        if self.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(
                f"Invalid LOG_LEVEL: {self.LOG_LEVEL}. Must be DEBUG, INFO, WARNING, ERROR, or CRITICAL."
            )

        if self.LOG_FORMAT not in ["json", "console"]:
            raise ValueError(
                f"Invalid LOG_FORMAT: {self.LOG_FORMAT}. Must be 'json' or 'console'."
            )

        if self.AGENT_TIMEOUT_SECONDS <= 0:
            raise ValueError("AGENT_TIMEOUT_SECONDS must be greater than 0")


config = Config()
