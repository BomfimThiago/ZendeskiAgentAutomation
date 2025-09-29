"""Simplified conversation state for LangGraph workflow."""

from typing import Annotated, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class ConversationState(TypedDict):
    """State object for TeleCorp customer support workflow with persona routing."""

    # Core LangGraph pattern - messages are the primary state
    messages: Annotated[list[BaseMessage], add_messages]

    # Simple context tracking
    user_id: Optional[str]
    session_id: Optional[str]

    # Persona routing state
    conversation_type: str  # "general", "sales", "support"
    current_persona: str    # "general_alex", "sales_alex"

    # Minimal metadata
    metadata: Dict[str, Any]