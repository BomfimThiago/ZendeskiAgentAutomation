"""
Simple application configuration using Pydantic Settings.

This module centralizes application settings and environment variables
for development use.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Zendesk Configuration
    ZENDESK_URL: str  # This will read from .env
    ZENDESK_TOKEN: str  # This will read from .env

    # API Configuration
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_HEADERS: list[str] = ["*"]

    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()