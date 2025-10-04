"""
Security-specific exceptions for LLM applications.

These exceptions provide clear, actionable error information when security
violations are detected.
"""
from typing import Optional, Dict, Any


class SecurityError(Exception):
    """Base exception for all security-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        mitigation: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.mitigation = mitigation
        super().__init__(self.message)

    def __str__(self) -> str:
        base = f"SecurityError: {self.message}"
        if self.mitigation:
            base += f"\nMitigation: {self.mitigation}"
        if self.details:
            base += f"\nDetails: {self.details}"
        return base


class PromptInjectionDetected(SecurityError):
    """Raised when prompt injection attack is detected in user input."""

    def __init__(
        self,
        message: str = "Prompt injection attack detected",
        attack_type: Optional[str] = None,
        confidence: float = 1.0,
        details: Optional[Dict[str, Any]] = None
    ):
        self.attack_type = attack_type
        self.confidence = confidence
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "attack_type": attack_type,
                "confidence": confidence
            },
            mitigation="Input has been blocked. Please rephrase your request."
        )


class DataExfiltrationAttempt(SecurityError):
    """Raised when data exfiltration attempt is detected."""

    def __init__(
        self,
        message: str = "Data exfiltration attempt detected",
        vector: Optional[str] = None,
        blocked_content: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.vector = vector
        self.blocked_content = blocked_content
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "vector": vector,
                "blocked_content": blocked_content
            },
            mitigation="Suspicious content has been removed from the response."
        )


class UnauthorizedToolAccess(SecurityError):
    """Raised when a tool is accessed without proper authorization."""

    def __init__(
        self,
        message: str = "Unauthorized tool access attempt",
        tool_name: Optional[str] = None,
        required_capability: Optional[str] = None,
        current_capability: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.tool_name = tool_name
        self.required_capability = required_capability
        self.current_capability = current_capability
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "tool_name": tool_name,
                "required_capability": required_capability,
                "current_capability": current_capability
            },
            mitigation="This operation requires manual approval."
        )


class QuarantineRequired(SecurityError):
    """Raised when input must be processed in quarantine (by untrusted LLM)."""

    def __init__(
        self,
        message: str = "Input requires quarantine processing",
        trust_score: Optional[float] = None,
        reasons: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.trust_score = trust_score
        self.reasons = reasons or []
        super().__init__(
            message=message,
            details={
                **(details or {}),
                "trust_score": trust_score,
                "reasons": reasons
            },
            mitigation="Input will be processed in isolated quarantine environment."
        )
