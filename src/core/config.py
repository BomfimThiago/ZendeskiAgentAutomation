"""
Simple application configuration using Pydantic Settings.

This module centralizes application settings and environment variables
for development use.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ZENDESK_URL: str = ""
    ZENDESK_TOKEN: str = ""
    ZENDESK_EMAIL: str = ""

    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = ""
    LANGSMITH_PROJECT: str = ""

    # API Configuration
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_HEADERS: list[str] = ["*"]

    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()