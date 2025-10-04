"""
LLM Security Module

A comprehensive, reusable security framework for LLM-based applications.
"""

# Core primitives
from .core.data_provenance import TrustLevel, DataProvenance
from .core.security_context import SecurityContext

# Exceptions
from .exceptions import (
    SecurityError,
    PromptInjectionDetected,
    DataExfiltrationAttempt,
    UnauthorizedToolAccess,
    QuarantineRequired
)

# Configuration
from .config import SecurityConfig, security_config

# Guardrails (Phase 1)
from .guardrails import (
    OutputSanitizer,
    PatternDetector,
    AttackType,
    InputValidator,
    ValidationResult
)

__all__ = [
    # Core
    "TrustLevel",
    "DataProvenance",
    "SecurityContext",
    
    # Exceptions
    "SecurityError",
    "PromptInjectionDetected",
    "DataExfiltrationAttempt",
    "UnauthorizedToolAccess",
    "QuarantineRequired",
    
    # Config
    "SecurityConfig",
    "security_config",
    
    # Guardrails
    "OutputSanitizer",
    "PatternDetector",
    "AttackType",
    "InputValidator",
    "ValidationResult",
]

__version__ = "1.0.0"
