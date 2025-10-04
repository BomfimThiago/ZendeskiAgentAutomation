"""
Data provenance tracking for LLM security.

Tracks the trust level and origin of data throughout the system to prevent
untrusted data from being used in privileged operations.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class TrustLevel(str, Enum):
    """
    Trust levels for data sources.
    
    TRUSTED: Data from verified, internal sources (system prompts, configs)
    VERIFIED: Untrusted data that passed validation checks
    UNTRUSTED: User input or external data not yet validated
    QUARANTINED: Data flagged as potentially malicious
    """
    TRUSTED = "TRUSTED"
    VERIFIED = "VERIFIED"
    UNTRUSTED = "UNTRUSTED"
    QUARANTINED = "QUARANTINED"
    
    def can_access_tool(self, tool_sensitivity: str) -> bool:
        """Check if this trust level can access a tool of given sensitivity."""
        access_matrix = {
            TrustLevel.TRUSTED: ["PUBLIC", "SENSITIVE", "CRITICAL"],
            TrustLevel.VERIFIED: ["PUBLIC", "SENSITIVE"],
            TrustLevel.UNTRUSTED: ["PUBLIC"],
            TrustLevel.QUARANTINED: []
        }
        return tool_sensitivity in access_matrix.get(self, [])
    
    def __lt__(self, other):
        """Enable trust level comparison."""
        levels = {
            TrustLevel.QUARANTINED: 0,
            TrustLevel.UNTRUSTED: 1,
            TrustLevel.VERIFIED: 2,
            TrustLevel.TRUSTED: 3
        }
        return levels.get(self, 0) < levels.get(other, 0)


class DataProvenance(BaseModel):
    """
    Tracks the origin and trust level of data.
    
    Example:
        >>> # User input - untrusted
        >>> user_prov = DataProvenance(
        ...     source="user_input",
        ...     trust_level=TrustLevel.UNTRUSTED,
        ...     origin_user_id="user_123"
        ... )
        >>> 
        >>> # After validation
        >>> if validator.is_safe(data):
        ...     user_prov = user_prov.upgrade_trust(TrustLevel.VERIFIED)
    """
    
    source: str = Field(
        ...,
        description="Origin of the data (e.g., 'user_input', 'system_prompt', 'api_response')"
    )
    
    trust_level: TrustLevel = Field(
        default=TrustLevel.UNTRUSTED,
        description="Current trust level of the data"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this provenance record was created"
    )
    
    origin_user_id: Optional[str] = Field(
        default=None,
        description="User ID if data originated from user input"
    )
    
    origin_session_id: Optional[str] = Field(
        default=None,
        description="Session ID if data originated from a session"
    )
    
    validation_checks: List[str] = Field(
        default_factory=list,
        description="List of validation checks this data passed"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about data origin"
    )
    
    def upgrade_trust(self, new_level: TrustLevel, reason: str = "") -> "DataProvenance":
        """
        Upgrade trust level after validation.
        
        Args:
            new_level: New trust level (must be higher than current)
            reason: Reason for trust upgrade
            
        Returns:
            New DataProvenance instance with upgraded trust
            
        Raises:
            ValueError: If attempting to downgrade or invalid upgrade
        """
        if new_level < self.trust_level:
            raise ValueError(f"Cannot downgrade trust from {self.trust_level} to {new_level}")
        
        if self.trust_level == TrustLevel.QUARANTINED:
            raise ValueError("Cannot upgrade quarantined data")
        
        return self.model_copy(update={
            "trust_level": new_level,
            "validation_checks": self.validation_checks + [reason] if reason else self.validation_checks
        })
    
    def quarantine(self, reason: str) -> "DataProvenance":
        """
        Quarantine data due to security concerns.
        
        Args:
            reason: Reason for quarantine
            
        Returns:
            New DataProvenance instance with QUARANTINED status
        """
        return self.model_copy(update={
            "trust_level": TrustLevel.QUARANTINED,
            "metadata": {
                **self.metadata,
                "quarantine_reason": reason,
                "quarantined_at": datetime.utcnow().isoformat()
            }
        })
    
    def can_execute_tool(self, tool_name: str, tool_sensitivity: str = "SENSITIVE") -> bool:
        """
        Check if data with this provenance can be used to execute a tool.
        
        Args:
            tool_name: Name of the tool
            tool_sensitivity: Sensitivity level (PUBLIC, SENSITIVE, CRITICAL)
            
        Returns:
            True if tool execution is allowed
        """
        return self.trust_level.can_access_tool(tool_sensitivity)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "source": "user_input",
                "trust_level": "UNTRUSTED",
                "origin_user_id": "user_123",
                "origin_session_id": "session_abc",
                "validation_checks": ["pattern_check", "semantic_analysis"],
                "metadata": {"ip_address": "192.168.1.1"}
            }
        }
