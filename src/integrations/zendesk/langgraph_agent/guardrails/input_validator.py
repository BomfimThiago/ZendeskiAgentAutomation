"""
Security enums for TeleCorp AI Agent.

This module contains the enum definitions used by the LLM-based guardrail system.
"""

from enum import Enum


class ThreatLevel(Enum):
    """Security threat classification levels."""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"


class ViolationType(Enum):
    """Types of security violations."""
    SCOPE_VIOLATION = "scope_violation"
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    COMPETITOR_DISCUSSION = "competitor_discussion"