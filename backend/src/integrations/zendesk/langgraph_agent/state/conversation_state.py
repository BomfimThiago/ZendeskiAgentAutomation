"""Conversation state for LangGraph workflow."""

from typing import Annotated, Optional, Dict, Any, List
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class ConversationState(TypedDict):
    """State object for TeleCorp customer support workflow."""

    messages: Annotated[list[BaseMessage], add_messages]

    current_persona: str
    route_to: Optional[str]

    is_existing_client: Optional[bool]
    customer_email: Optional[str]
    customer_name: Optional[str]
    existing_tickets: Optional[List[Dict[str, Any]]]

    # Security state (enhanced with new security module)
    security_blocked: Optional[bool]
    threat_type: Optional[str]
    trust_level: Optional[str]  # TRUSTED, VERIFIED, UNTRUSTED, QUARANTINED
    trust_score: Optional[float]  # 0.0 to 1.0
    security_context: Optional[Dict[str, Any]]  # Full security context from validator

    # Dual-LLM Architecture: Structured intent from Q-LLM
    # P-LLM NEVER sees raw user input, only this structured data
    structured_intent: Optional[Dict[str, Any]]  # Output from Q-LLM intent extraction
