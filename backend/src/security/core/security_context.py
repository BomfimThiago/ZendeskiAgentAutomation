"""
Security context for request processing.

Maintains security state throughout request lifecycle.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from .data_provenance import TrustLevel, DataProvenance


class SecurityContext(BaseModel):
    """
    Security context for a request or operation.
    
    Tracks trust levels, user identity, and security decisions throughout
    the request lifecycle.
    
    Example:
        >>> context = SecurityContext(
        ...     user_id="user_123",
        ...     session_id="session_abc",
        ...     trust_level=TrustLevel.UNTRUSTED
        ... )
        >>> 
        >>> # After validation
        >>> if validation_passed:
        ...     context = context.upgrade_trust(TrustLevel.VERIFIED)
    """
    
    # Unique identifiers
    context_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for this security context"
    )
    
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID if part of HTTP request"
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="User ID making the request"
    )
    
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID"
    )
    
    # Trust and provenance
    trust_level: TrustLevel = Field(
        default=TrustLevel.UNTRUSTED,
        description="Current trust level of the request"
    )
    
    data_provenance: Optional[DataProvenance] = Field(
        default=None,
        description="Detailed provenance information"
    )
    
    # Security checks
    validation_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from various validation checks"
    )
    
    security_flags: List[str] = Field(
        default_factory=list,
        description="Security flags raised during processing"
    )
    
    blocked_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons why operations were blocked"
    )
    
    # Capabilities and permissions
    granted_capabilities: List[str] = Field(
        default_factory=list,
        description="Capabilities granted to this context"
    )
    
    approved_tools: List[str] = Field(
        default_factory=list,
        description="Tools approved for use in this context"
    )
    
    # Timing and metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When context was created"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context metadata"
    )
    
    def upgrade_trust(self, new_level: TrustLevel, reason: str = "") -> "SecurityContext":
        """Upgrade trust level after validation."""
        if new_level < self.trust_level:
            raise ValueError(f"Cannot downgrade trust from {self.trust_level} to {new_level}")
        
        return self.model_copy(update={
            "trust_level": new_level,
            "security_flags": self.security_flags + [f"trust_upgraded: {reason}"] if reason else self.security_flags
        })
    
    def add_security_flag(self, flag: str, details: Optional[Dict[str, Any]] = None) -> "SecurityContext":
        """Add a security flag to this context."""
        flag_entry = flag
        if details:
            flag_entry = f"{flag}: {details}"
        
        return self.model_copy(update={
            "security_flags": self.security_flags + [flag_entry]
        })
    
    def block_operation(self, reason: str) -> "SecurityContext":
        """Block an operation for security reasons."""
        return self.model_copy(update={
            "blocked_reasons": self.blocked_reasons + [reason]
        })
    
    def grant_capability(self, capability: str) -> "SecurityContext":
        """Grant a capability to this context."""
        if capability not in self.granted_capabilities:
            return self.model_copy(update={
                "granted_capabilities": self.granted_capabilities + [capability]
            })
        return self
    
    def approve_tool(self, tool_name: str) -> "SecurityContext":
        """Approve a tool for use."""
        if tool_name not in self.approved_tools:
            return self.model_copy(update={
                "approved_tools": self.approved_tools + [tool_name]
            })
        return self
    
    def can_execute_tool(self, tool_name: str) -> bool:
        """Check if a tool can be executed in this context."""
        # Tool must be explicitly approved OR trust level must be TRUSTED
        return tool_name in self.approved_tools or self.trust_level == TrustLevel.TRUSTED
    
    def has_capability(self, capability: str) -> bool:
        """Check if context has a specific capability."""
        return capability in self.granted_capabilities
    
    def is_blocked(self) -> bool:
        """Check if any operations have been blocked."""
        return len(self.blocked_reasons) > 0
    
    def to_log_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging."""
        return {
            "context_id": self.context_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "trust_level": self.trust_level,
            "security_flags": self.security_flags,
            "blocked_reasons": self.blocked_reasons,
            "created_at": self.created_at.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (full serialization)."""
        return self.model_dump(mode='python')

    class Config:
        """Pydantic config."""
        use_enum_values = True
