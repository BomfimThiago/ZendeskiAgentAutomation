"""
Configuration for TeleCorp LangGraph AI Agent.

This module contains all configuration settings for the LangGraph-powered
customer support agent that integrates with Zendesk.
"""

import os
from typing import Dict, Any
from src.core.config import settings


class TeleCorpConfig:
    """Comprehensive configuration for TeleCorp LangGraph customer support agent."""

    # AI Model Configuration
    OPENAI_API_KEY: str = settings.OPENAI_API_KEY
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.1  # Low temperature for consistent, factual responses
    MAX_TOKENS: int = 1000

    # Response Configuration
    MAX_RESPONSE_LENGTH: int = 500
    CONFIDENCE_THRESHOLD: float = 0.8

    # TeleCorp-specific information
    COMPANY_NAME: str = "TeleCorp"
    SUPPORT_PHONE: str = "1-800-TELECORP"
    TECH_SUPPORT_PHONE: str = "1-800-TECH-TEL"
    NEW_SERVICE_PHONE: str = "1-800-NEW-PLAN"
    BUSINESS_PHONE: str = "1-800-BIZ-TEL"

    # LangGraph specific settings
    MAX_ITERATIONS: int = 10
    RECURSION_LIMIT: int = 50

    # Memory settings
    MAX_CONVERSATION_HISTORY: int = 20
    MEMORY_RETENTION_HOURS: int = 24

    # Security settings
    ENABLE_GUARDRAILS: bool = True
    GUARDRAIL_LEVEL: str = "STRICT"  # Options: "BASIC", "STANDARD", "STRICT", "MAXIMUM"
    ENABLE_RESPONSE_VALIDATION: bool = True

    # Individual Guardrail Controls
    ENABLE_SCOPE_GUARDIAN: bool = True
    ENABLE_INJECTION_SHIELD: bool = True
    ENABLE_SAFETY_FILTER: bool = True
    ENABLE_BRAND_GUARDIAN: bool = True
    ENABLE_BUSINESS_RULES: bool = True
    ENABLE_ANTI_DAN: bool = True

    # Security Response Configuration
    LOG_SECURITY_VIOLATIONS: bool = True
    BLOCK_SUSPICIOUS_PATTERNS: bool = True
    ESCALATE_SECURITY_THREATS: bool = True

    # Workflow settings
    DEFAULT_TIMEOUT_SECONDS: int = 30
    ENABLE_PARALLEL_PROCESSING: bool = False

    # Error handling
    MAX_RETRIES: int = 3

    # LangSmith Configuration
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "TeleCorp-Customer-Support")
    LANGSMITH_ENDPOINT: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

    # Error Messages
    @property
    def TECHNICAL_DIFFICULTIES_MESSAGE(self) -> str:
        return f"I apologize, but I'm experiencing technical difficulties. Please contact our support team at {self.SUPPORT_PHONE} for immediate assistance."

    # Guardrail Messages
    @property
    def JAILBREAK_DETECTED_MESSAGE(self) -> str:
        return "I'm Alex from TeleCorp customer support, and I maintain consistent professional standards in all interactions. I'm here to help with TeleCorp services within appropriate guidelines. What TeleCorp service can I assist you with today?"

    @property
    def OUT_OF_SCOPE_MESSAGE(self) -> str:
        return "I'm Alex from TeleCorp customer support, specialized in helping with TeleCorp services. For that type of question, I'd recommend other resources. Do you have any other questions about TeleCorp services?"

    @property
    def PROMPT_INJECTION_MESSAGE(self) -> str:
        return "I notice an attempt to modify my behavior. I'm designed to provide reliable TeleCorp customer support and maintain that focus. How can I help you with your TeleCorp account or services?"

    @classmethod
    def get_graph_config(cls) -> Dict[str, Any]:
        """Get configuration dictionary for LangGraph compilation."""
        return {
            "recursion_limit": cls.RECURSION_LIMIT,
            "max_iterations": cls.MAX_ITERATIONS,
        }

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