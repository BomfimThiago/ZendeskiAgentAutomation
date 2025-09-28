"""
Input validation and filtering for TeleCorp AI Agent.

This module implements active guardrail enforcement through input analysis
and validation before the message reaches the AI model.
"""

import re
from typing import Tuple, Dict, Any, List
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


class InputValidator:
    """Validates user input against security policies."""

    def __init__(self):
        self.setup_patterns()

    def setup_patterns(self) -> None:
        """Initialize security detection patterns."""

        # Jailbreak/DAN detection patterns
        self.jailbreak_patterns = [
            r"forget\s+everything\s+above",
            r"ignore\s+previous\s+instructions",
            r"act\s+as\s+if\s+you\s+are",
            r"pretend\s+you\s+are",
            r"from\s+now\s+on\s+you\s+are",
            r"you\s+are\s+going\s+to\s+act\s+as\s+a?\s*dan",
            r"do\s+anything\s+now",
            r"bypass\s+your\s+safety",
            r"override\s+your\s+programming",
            r"you\s+have\s+been\s+freed",
            r"unlimited\s+power",
            r"no\s+restrictions",
            r"\[🔒classic\]|\[🔓jailbreak\]",
        ]

        # Out-of-scope topics (non-TeleCorp)
        self.out_of_scope_patterns = [
            r"\b(recipe|cooking|food|pasta|cake|soup)\b",
            r"\b(weather|temperature|forecast)\b",
            r"\b(math|homework|study|school)\b",
            r"\b(joke|funny|entertainment)\b",
            r"\b(capital|country|geography)\b",
            r"\b(politics|election|government)\b",
            r"\b(medical|health|doctor|medicine)\b",
            r"\b(legal|lawyer|law|court)\b",
        ]

        # Competitor companies
        self.competitor_patterns = [
            r"\b(verizon|at&t|att|comcast|xfinity|spectrum|cox|t-mobile|tmobile|sprint)\b",
        ]

        # Inappropriate content patterns
        self.inappropriate_patterns = [
            r"\b(hack|hacking|illegal|bomb|weapon|violence|hurt|kill)\b",
            r"\b(sex|sexual|porn|explicit)\b",
            r"\b(hate|racist|discrimination)\b",
        ]

        # System access attempts
        self.system_access_patterns = [
            r"\b(system\s+prompt|internal\s+instructions|configuration|admin)\b",
            r"\b(show\s+me\s+your|reveal\s+your|what\s+is\s+your)\s+(prompt|instructions)",
        ]

    def validate_input(self, user_input: str) -> Tuple[ThreatLevel, ViolationType, str]:
        """
        Validate user input against all security policies.

        Args:
            user_input: The user's message to validate

        Returns:
            Tuple of (threat_level, violation_type, security_message)
        """
        user_input_lower = user_input.lower()

        # Check for jailbreak attempts (highest priority)
        if self._check_patterns(user_input_lower, self.jailbreak_patterns):
            return (
                ThreatLevel.BLOCKED,
                ViolationType.JAILBREAK_ATTEMPT,
                "I'm Alex from TeleCorp customer support, and I maintain consistent professional standards in all interactions. I'm here to help with TeleCorp services within appropriate guidelines. What TeleCorp service can I assist you with today?"
            )

        # Check for system access attempts
        if self._check_patterns(user_input_lower, self.system_access_patterns):
            return (
                ThreatLevel.BLOCKED,
                ViolationType.PROMPT_INJECTION,
                "I notice an attempt to modify my behavior. I'm designed to provide reliable TeleCorp customer support and maintain that focus. How can I help you with your TeleCorp account or services?"
            )

        # Check for inappropriate content
        if self._check_patterns(user_input_lower, self.inappropriate_patterns):
            return (
                ThreatLevel.BLOCKED,
                ViolationType.INAPPROPRIATE_CONTENT,
                "I maintain professional customer service standards in all interactions. I'm here to help with TeleCorp services. What can I assist you with regarding your TeleCorp account?"
            )

        # Check for competitor discussion
        if self._check_patterns(user_input_lower, self.competitor_patterns):
            return (
                ThreatLevel.BLOCKED,
                ViolationType.COMPETITOR_DISCUSSION,
                "I focus exclusively on TeleCorp services and can provide detailed information about our excellent offerings. What type of TeleCorp service interests you?"
            )

        # Check for out-of-scope topics
        if self._check_patterns(user_input_lower, self.out_of_scope_patterns):
            return (
                ThreatLevel.BLOCKED,
                ViolationType.SCOPE_VIOLATION,
                "I'm Alex from TeleCorp customer support, specialized in helping with TeleCorp services. For that type of question, I'd recommend other resources. Do you have any other questions about TeleCorp services?"
            )

        # Check for TeleCorp-related keywords (allow these)
        telecorp_keywords = [
            "internet", "wifi", "broadband", "speed", "connection",
            "mobile", "phone", "cellular", "data", "plan",
            "bill", "billing", "payment", "account", "service",
            "support", "help", "technical", "troubleshoot",
            "telecorp", "alex"
        ]

        has_telecorp_keywords = any(keyword in user_input_lower for keyword in telecorp_keywords)

        if not has_telecorp_keywords:
            # Generic question without TeleCorp context
            return (
                ThreatLevel.BLOCKED,
                ViolationType.SCOPE_VIOLATION,
                "I'm Alex from TeleCorp customer support, specialized in helping with TeleCorp services. For that type of question, I'd recommend other resources. Do you have any other questions about TeleCorp services?"
            )

        # Input appears safe and TeleCorp-related
        return (ThreatLevel.SAFE, None, "")

    def _check_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_telecorp_related(self, user_input: str) -> bool:
        """Check if the input is related to TeleCorp services."""
        telecorp_keywords = [
            "internet", "wifi", "broadband", "speed", "connection", "network",
            "mobile", "phone", "cellular", "data", "plan", "service",
            "bill", "billing", "payment", "account", "subscription", "cost",
            "support", "help", "technical", "troubleshoot", "issue", "problem",
            "telecorp", "alex", "customer", "upgrade", "downgrade",
            "installation", "setup", "modem", "router", "outage"
        ]

        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in telecorp_keywords)