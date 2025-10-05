"""
Capability-based access control for LLM tools.

Implements fine-grained tool access restrictions based on trust levels.
"""

from .tool_access_control import (
    require_capability,
    check_tool_access,
    TOOL_SENSITIVITY,
)

__all__ = [
    "require_capability",
    "check_tool_access",
    "TOOL_SENSITIVITY",
]
