"""
Configuration for MyAwesomeFakeCompany LangGraph AI Agent.

This module contains all configuration settings for the LangGraph-powered
customer support agent that integrates with Zendesk.
"""

from src.core.config import settings


class AwesomeCompanyConfig:
    """Configuration for MyAwesomeFakeCompany LangGraph customer support agent."""

    OPENAI_API_KEY: str = settings.OPENAI_API_KEY
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 1000

    COMPANY_NAME: str = "MyAwesomeFakeCompany"
    SUPPORT_PHONE: str = "1-800-AWESOME-COMPANY"

    MAX_ITERATIONS: int = 10
    RECURSION_LIMIT: int = 50

    ENABLE_GUARDRAILS: bool = True

    @classmethod
    def validate_config(cls) -> None:
        """Validate all required configuration values."""
        # Only require OPENAI_API_KEY if not using Bedrock
        if not settings.USE_BEDROCK and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables (required when USE_BEDROCK=false)")

        if not cls.DEFAULT_MODEL:
            raise ValueError("DEFAULT_MODEL not configured")


# Global configuration instance
awesome_company_config = AwesomeCompanyConfig()
awesome_company_config.validate_config()
