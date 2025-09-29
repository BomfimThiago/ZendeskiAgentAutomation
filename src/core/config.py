"""
Simple application configuration using Pydantic Settings.

This module centralizes application settings and environment variables
for development use.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ZENDESK_URL: str = ""
    ZENDESK_TOKEN: str = ""
    ZENDESK_EMAIL: str = ""

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""

    # LangSmith Configuration - supporting both old and new variable names
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = ""
    LANGCHAIN_ENDPOINT: str = ""

    # Legacy LangSmith variables (for backward compatibility)
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = ""
    LANGSMITH_ENDPOINT: str = ""

    # API Configuration
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_HEADERS: list[str] = ["*"]

    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields to handle any unexpected variables


settings = Settings()


def setup_langsmith():
    """Set up LangSmith environment variables for tracing."""
    # Use new variables first, then fall back to legacy ones for backward compatibility

    # Enable tracing if either new or old variable is set
    enable_tracing = settings.LANGCHAIN_TRACING_V2 or settings.LANGSMITH_TRACING
    if enable_tracing:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

    # Use API key from either source
    api_key = settings.LANGCHAIN_API_KEY or settings.LANGSMITH_API_KEY
    if api_key:
        os.environ["LANGCHAIN_API_KEY"] = api_key

    # Use project from either source
    project = settings.LANGCHAIN_PROJECT or settings.LANGSMITH_PROJECT
    if project:
        os.environ["LANGCHAIN_PROJECT"] = project

    # Use endpoint from either source
    endpoint = settings.LANGCHAIN_ENDPOINT or settings.LANGSMITH_ENDPOINT
    if endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint