"""Conversation state management for LangGraph workflow."""

from typing import Annotated, Optional, List, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage

from .schemas import SecurityThreat, TicketContext, UserContext, ConversationMessage


class ConversationState(TypedDict):
    """Main state object for TeleCorp customer support workflow."""

    messages: Annotated[List[BaseMessage], add_messages]
    user_input: str
    assistant_response: str

    session_key: str
    ticket_id: Optional[str]
    user_id: Optional[str]

    security_check: Optional[SecurityThreat]
    is_secure: bool

    ticket_context: Optional[TicketContext]
    user_context: Optional[UserContext]

    conversation_history: List[ConversationMessage]
    memory_loaded: bool

    route_decision: str  # "ticket_lookup", "direct_chat", "escalation"
    requires_zendesk_update: bool

    final_response: str
    response_validated: bool

    error_occurred: bool
    error_message: str

    workflow_step: str
    processing_time: float
    metadata: Dict[str, Any]