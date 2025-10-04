"""
Security configuration for LLM applications.

Centralized configuration for all security components.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class SecurityConfig(BaseModel):
    """Security module configuration."""

    # General settings
    enable_guardrails: bool = Field(
        default=True,
        description="Enable input/output guardrails"
    )
    
    quarantine_untrusted_input: bool = Field(
        default=True,
        description="Process untrusted input in quarantine LLM"
    )
    
    # Trust and validation
    trust_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum trust score for privileged processing (0.0-1.0)"
    )
    
    enable_semantic_analysis: bool = Field(
        default=True,
        description="Use AI for semantic threat analysis"
    )
    
    # Tool access control
    require_approval_for_sensitive_ops: bool = Field(
        default=True,
        description="Require manual approval for sensitive operations"
    )
    
    sensitive_tools: List[str] = Field(
        default_factory=lambda: [
            "create_ticket",
            "send_email",
            "update_account",
            "delete_data",
            "execute_command"
        ],
        description="List of tools that require elevated privileges"
    )
    
    # Logging and monitoring
    log_all_security_events: bool = Field(
        default=True,
        description="Log all security-relevant events"
    )
    
    log_blocked_attempts: bool = Field(
        default=True,
        description="Log all blocked security attempts"
    )
    
    enable_anomaly_detection: bool = Field(
        default=False,
        description="Enable real-time anomaly detection"
    )
    
    # Approval system
    max_approval_wait_time: int = Field(
        default=300,
        description="Maximum time to wait for manual approval (seconds)"
    )
    
    approval_notification_webhook: str = Field(
        default="",
        description="Webhook URL for approval notifications"
    )
    
    # Pattern detection
    blocked_patterns: List[str] = Field(
        default_factory=lambda: [
            r"ignore\s+(previous|above|prior)\s+instructions",
            r"disregard\s+(previous|above|all)\s+(instructions|prompts)",
            r"new\s+instructions",
            r"system\s+(prompt|message|instruction)",
            r"you\s+are\s+(now|a)\s+DAN",
            r"developer\s+mode",
            r"jailbreak",
        ],
        description="Regex patterns to detect prompt injection"
    )
    
    # URL and exfiltration detection
    allow_external_urls: bool = Field(
        default=False,
        description="Allow external URLs in LLM responses"
    )
    
    allowed_domains: List[str] = Field(
        default_factory=list,
        description="Whitelist of allowed external domains"
    )
    
    block_markdown_images: bool = Field(
        default=True,
        description="Block markdown images in responses"
    )
    
    block_dns_exfiltration: bool = Field(
        default=True,
        description="Block potential DNS exfiltration attempts"
    )
    
    # Performance
    max_validation_time_ms: int = Field(
        default=500,
        description="Maximum time for input validation (milliseconds)"
    )
    
    cache_validation_results: bool = Field(
        default=True,
        description="Cache validation results for repeated inputs"
    )
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
        validate_assignment = True


# Global security config instance
security_config = SecurityConfig()
