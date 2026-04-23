"""LLM dependency injection for FastAPI."""
from functools import lru_cache

import structlog
from langchain_openai import ChatOpenAI

from core.config import config


logger = structlog.get_logger("docintel.dependencies.llm")


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    """
    Get configured LLM instance (cached singleton).
    
    Returns:
        ChatOpenAI instance configured for the selected provider.
        
    Raises:
        ValueError: If LLM_PROVIDER is not supported.
    """
    logger.info("llm_initialization_started", provider=config.LLM_PROVIDER)
    
    if config.LLM_PROVIDER == "groq":
        llm = ChatOpenAI(
            model=config.GROQ_MODEL,
            api_key=config.GROQ_API_KEY,
            base_url=config.GROQ_BASE_URL,
            streaming=True,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=2048,
        )
        logger.info("llm_initialized", provider="groq", model=config.GROQ_MODEL)
        return llm

    if config.LLM_PROVIDER == "lmstudio":
        llm = ChatOpenAI(
            model=config.LMSTUDIO_MODEL,
            api_key=config.LMSTUDIO_API_KEY,
            base_url=config.LMSTUDIO_BASE_URL,
            streaming=True,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=2048,
        )
        logger.info("llm_initialized", provider="lmstudio", model=config.LMSTUDIO_MODEL)
        return llm

    raise ValueError(
        f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER}. Use 'groq' or 'lmstudio'."
    )
