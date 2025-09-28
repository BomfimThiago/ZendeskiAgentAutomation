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

    # Guardrail Configuration
    ENABLE_GUARDRAILS: bool = True
    GUARDRAIL_LEVEL: str = "STRICT"  # Options: "BASIC", "STANDARD", "STRICT", "MAXIMUM"

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

    # System prompt will use the TeleCorp persona from prompts/telecorp_persona.py


# Global configuration instance
ai_config = ZendeskAIConfig()