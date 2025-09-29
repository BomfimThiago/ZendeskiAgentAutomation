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

    security_blocked: Optional[bool]
    threat_type: Optional[str]
