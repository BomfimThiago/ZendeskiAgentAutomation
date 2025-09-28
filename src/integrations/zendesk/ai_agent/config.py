"""
Configuration for Zendesk AI Agent.

This module contains configuration settings for the AI-powered customer support agent
that integrates with Zendesk for enhanced ticket management and customer service.
"""

from src.core.config import settings


class ZendeskAIConfig:
    """Configuration for Zendesk AI Agent."""

    # AI Model Configuration
    OPENAI_API_KEY: str = settings.OPENAI_API_KEY
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.1  # Low temperature for consistent, factual responses
    MAX_TOKENS: int = 1000

    # Response Configuration
    MAX_RESPONSE_LENGTH: int = 500
    CONFIDENCE_THRESHOLD: float = 0.8 #  Only answer if AI is 80%+ confiden, if not escale to human agent

    # TeleCorp-specific information
    COMPANY_NAME: str = "TeleCorp"
    SUPPORT_PHONE: str = "1-800-TELECORP"
    TECH_SUPPORT_PHONE: str = "1-800-TECH-TEL"
    NEW_SERVICE_PHONE: str = "1-800-NEW-PLAN"
    BUSINESS_PHONE: str = "1-800-BIZ-TEL"

    # Error Messages
    @property
    def TECHNICAL_DIFFICULTIES_MESSAGE(self) -> str:
        return f"I apologize, but I'm experiencing technical difficulties. Please contact our support team at {self.SUPPORT_PHONE} for immediate assistance."

    # System prompt will use the TeleCorp persona from prompts/telecorp_persona.py


# Global configuration instance
ai_config = ZendeskAIConfig()