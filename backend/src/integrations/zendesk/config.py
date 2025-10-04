"""
Zendesk-specific configuration and constants.

This module contains Zendesk API configuration, rate limiting settings,
and other constants specific to Zendesk integration.
"""
from pydantic_settings import BaseSettings

from src.core.config import settings


class ZendeskConfig:
    """Zendesk API configuration and constants."""

    BASE_URL: str = f"https://{settings.ZENDESK_URL}"
    API_VERSION: str = "v2"

    @property
    def api_url(self) -> str:
        """Get the full API URL."""
        return f"{self.BASE_URL}/api/{self.API_VERSION}"

    EMAIL: str = settings.ZENDESK_EMAIL
    TOKEN: str = settings.ZENDESK_TOKEN

    RATE_LIMIT_PER_MINUTE: int = 700  # Zendesk allows 700 requests per minute
    RATE_LIMIT_RETRY_AFTER: int = 60  # Default retry after seconds

    REQUEST_TIMEOUT: int = 30  # 30 seconds timeout
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 1.0

    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 100  # Zendesk max


# Global instance
zendesk_config = ZendeskConfig()