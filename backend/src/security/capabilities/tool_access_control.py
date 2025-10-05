"""
Capability-based tool access control.

Implements the capability model from the CaMeL paper - restricts tool
access based on data trust level and security context.

Key Principle: "Untrusted data should not be able to invoke privileged operations"
"""

from functools import wraps
from typing import Callable, Optional, Union
import inspect

from ..core.data_provenance import TrustLevel
from ..core.security_context import SecurityContext
from ..exceptions import UnauthorizedToolAccess
from src.core.logging_config import get_logger

logger = get_logger("tool_access_control")


def _get_trust_level_str(trust_level: Union[TrustLevel, str]) -> str:
    """Safely get string value from TrustLevel enum or string."""
    if hasattr(trust_level, 'value'):
        return trust_level.value
    return str(trust_level)


# Tool sensitivity levels
TOOL_SENSITIVITY = {
    # HIGH SENSITIVITY - Requires VERIFIED or higher trust
    "create_ticket": TrustLevel.VERIFIED,
    "create_support_ticket": TrustLevel.VERIFIED,
    "create_sales_ticket": TrustLevel.VERIFIED,
    "send_email": TrustLevel.VERIFIED,
    "update_customer_data": TrustLevel.TRUSTED,
    "delete_ticket": TrustLevel.TRUSTED,
    "refund_payment": TrustLevel.TRUSTED,

    # MEDIUM SENSITIVITY - Requires UNTRUSTED or higher
    "search_knowledge_base": TrustLevel.UNTRUSTED,
    "get_plans": TrustLevel.UNTRUSTED,
    "search_tickets": TrustLevel.UNTRUSTED,

    # LOW SENSITIVITY - Even QUARANTINED can access (but usually they don't have tools)
    "get_public_info": TrustLevel.QUARANTINED,
}


def require_capability(
    tool_name: str,
    required_trust: Optional[TrustLevel] = None
):
    """
    Decorator to enforce capability-based access control on tools.

    Usage:
        @require_capability("create_ticket")
        def create_support_ticket(context: SecurityContext, ...):
            # Only executed if context.trust_level >= VERIFIED
            ...

    Args:
        tool_name: Name of the tool (used for logging)
        required_trust: Minimum trust level required (defaults to TOOL_SENSITIVITY)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract SecurityContext from kwargs or args
            context = kwargs.get('security_context') or kwargs.get('context')

            if context is None:
                # Try to find it in args
                for arg in args:
                    if isinstance(arg, SecurityContext):
                        context = arg
                        break

            if context is None:
                # No security context provided - allow but log warning
                logger.warning(
                    f"Tool {tool_name} called without SecurityContext - SECURITY BYPASS RISK",
                    extra={"tool": tool_name}
                )
                return await func(*args, **kwargs)

            # Determine required trust level
            min_trust = required_trust or TOOL_SENSITIVITY.get(
                tool_name, TrustLevel.VERIFIED
            )

            # Check if context has sufficient trust
            if context.trust_level < min_trust:
                logger.error(
                    f"Unauthorized tool access blocked",
                    extra={
                        "tool": tool_name,
                        "required_trust": _get_trust_level_str(min_trust),
                        "actual_trust": _get_trust_level_str(context.trust_level),
                        "user_id": context.user_id,
                        "session_id": context.session_id
                    }
                )
                raise UnauthorizedToolAccess(
                    f"Tool '{tool_name}' requires trust level {_get_trust_level_str(min_trust)}, "
                    f"but context has {_get_trust_level_str(context.trust_level)}"
                )

            # Check if tool is explicitly approved
            if not context.can_execute_tool(tool_name):
                logger.error(
                    f"Tool not in approved list",
                    extra={
                        "tool": tool_name,
                        "approved_tools": context.approved_tools,
                        "trust_level": _get_trust_level_str(context.trust_level)
                    }
                )
                raise UnauthorizedToolAccess(
                    f"Tool '{tool_name}' not approved for this security context"
                )

            # Log successful authorization
            logger.info(
                f"Tool access authorized",
                extra={
                    "tool": tool_name,
                    "trust_level": _get_trust_level_str(context.trust_level),
                    "user_id": context.user_id
                }
            )

            # Execute tool
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract SecurityContext
            context = kwargs.get('security_context') or kwargs.get('context')

            if context is None:
                for arg in args:
                    if isinstance(arg, SecurityContext):
                        context = arg
                        break

            if context is None:
                logger.warning(
                    f"Tool {tool_name} called without SecurityContext - SECURITY BYPASS RISK"
                )
                return func(*args, **kwargs)

            # Determine required trust level
            min_trust = required_trust or TOOL_SENSITIVITY.get(
                tool_name, TrustLevel.VERIFIED
            )

            # Check trust level
            if context.trust_level < min_trust:
                logger.error(
                    f"Unauthorized tool access blocked",
                    extra={
                        "tool": tool_name,
                        "required_trust": _get_trust_level_str(min_trust),
                        "actual_trust": _get_trust_level_str(context.trust_level)
                    }
                )
                raise UnauthorizedToolAccess(
                    f"Tool '{tool_name}' requires trust level {_get_trust_level_str(min_trust)}, "
                    f"but context has {_get_trust_level_str(context.trust_level)}"
                )

            # Check if tool is approved
            if not context.can_execute_tool(tool_name):
                raise UnauthorizedToolAccess(
                    f"Tool '{tool_name}' not approved for this security context"
                )

            logger.info(f"Tool access authorized: {tool_name}")
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def check_tool_access(
    tool_name: str,
    context: SecurityContext,
    required_trust: Optional[TrustLevel] = None
) -> bool:
    """
    Check if a tool can be accessed with the given security context.

    Returns:
        True if access is allowed, False otherwise
    """
    min_trust = required_trust or TOOL_SENSITIVITY.get(
        tool_name, TrustLevel.VERIFIED
    )

    if context.trust_level < min_trust:
        return False

    return context.can_execute_tool(tool_name)
