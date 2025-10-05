"""
Secure tool executor with capability-based access control.

Wraps tool execution to enforce trust-based restrictions.
"""

from typing import Any, Dict
from src.security import (
    SecurityContext,
    TrustLevel,
    UnauthorizedToolAccess,
    TOOL_SENSITIVITY,
)
from src.core.logging_config import get_logger

logger = get_logger("secure_tool_executor")


async def execute_tool_securely(
    tool_func: Any,
    tool_name: str,
    tool_args: Dict[str, Any],
    security_context: Dict[str, Any],
) -> str:
    """
    Execute a tool with capability-based access control.

    Args:
        tool_func: The tool function to execute
        tool_name: Name of the tool
        tool_args: Arguments for the tool
        security_context: Security context dict from state

    Returns:
        Tool execution result

    Raises:
        UnauthorizedToolAccess: If trust level insufficient
    """
    # Extract trust level from security context
    trust_level_str = security_context.get("trust_level", "QUARANTINED")

    # Map string to TrustLevel enum
    trust_level_map = {
        "TRUSTED": TrustLevel.TRUSTED,
        "VERIFIED": TrustLevel.VERIFIED,
        "UNTRUSTED": TrustLevel.UNTRUSTED,
        "QUARANTINED": TrustLevel.QUARANTINED,
    }

    trust_level = trust_level_map.get(trust_level_str, TrustLevel.QUARANTINED)

    # Get required trust level for this tool
    required_trust = TOOL_SENSITIVITY.get(tool_name, TrustLevel.VERIFIED)

    # Check if trust level is sufficient
    if trust_level < required_trust:
        logger.error(
            f"🔒 CAPABILITY BLOCKED: {tool_name}",
            extra={
                "layer": "CAPABILITY_ENFORCEMENT",
                "tool": tool_name,
                "required_trust": required_trust.value,
                "actual_trust": trust_level.value,
                "user_id": security_context.get("user_id"),
                "action": "DENIED",
            },
        )
        raise UnauthorizedToolAccess(
            f"Tool '{tool_name}' requires trust level {required_trust.value}, "
            f"but context has {trust_level.value}"
        )

    # Log successful authorization
    logger.info(
        f"🔓 CAPABILITY ALLOWED: {tool_name}",
        extra={
            "layer": "CAPABILITY_ENFORCEMENT",
            "tool": tool_name,
            "trust_level": trust_level.value,
            "required_trust": required_trust.value,
            "action": "ALLOWED",
        },
    )

    # Execute tool
    try:
        result = await tool_func.ainvoke(tool_args)
        logger.info(
            f"✅ TOOL EXECUTED: {tool_name}",
            extra={
                "tool": tool_name,
                "trust_level": trust_level.value,
                "execution": "SUCCESS",
            },
        )
        return result
    except Exception as e:
        logger.error(
            f"❌ TOOL EXECUTION ERROR: {tool_name}",
            extra={
                "tool": tool_name,
                "error": str(e),
                "execution": "FAILED",
            }
        )
        raise
