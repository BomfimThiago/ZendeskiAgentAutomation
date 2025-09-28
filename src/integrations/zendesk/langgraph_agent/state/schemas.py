"""Pydantic schemas for TeleCorp LangGraph Agent."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Import the enums from guardrails to avoid duplication
from ..guardrails.input_validator import ThreatLevel, ViolationType


class SecurityThreat(BaseModel):
    """Security threat assessment result."""
    threat_level: ThreatLevel
    violation_type: Optional[ViolationType] = None
    security_message: str = ""
    blocked: bool = False


class TicketContext(BaseModel):
    """Zendesk ticket context information."""
    ticket_id: str
    status: str
    priority: str
    subject: str
    description: str
    customer_id: str
    comments: List[Dict[str, Any]] = []
    custom_fields: Dict[str, Any] = {}


class UserContext(BaseModel):
    """User/customer context information."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    account_type: Optional[str] = None
    service_plan: Optional[str] = None
    previous_tickets: List[str] = []


class ConversationMessage(BaseModel):
    """Individual conversation message."""
    role: str  # "human" or "assistant"
    content: str
    timestamp: str
    metadata: Dict[str, Any] = {}