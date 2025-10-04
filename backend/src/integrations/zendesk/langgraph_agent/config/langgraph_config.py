"""
Configuration for TeleCorp LangGraph AI Agent.

This module contains all configuration settings for the LangGraph-powered
customer support agent that integrates with Zendesk.
"""

from src.core.config import settings


class TeleCorpConfig:
    """Configuration for TeleCorp LangGraph customer support agent."""

    OPENAI_API_KEY: str = settings.OPENAI_API_KEY
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1000

    COMPANY_NAME: str = "TeleCorp"
    SUPPORT_PHONE: str = "1-800-TELECORP"

    MAX_ITERATIONS: int = 10
    RECURSION_LIMIT: int = 50

    ENABLE_GUARDRAILS: bool = True

    @classmethod
    def validate_config(cls) -> None:
        """Validate all required configuration values."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        if not cls.DEFAULT_MODEL:
            raise ValueError("DEFAULT_MODEL not configured")


# Global configuration instance
telecorp_config = TeleCorpConfig()
telecorp_config.validate_config()
