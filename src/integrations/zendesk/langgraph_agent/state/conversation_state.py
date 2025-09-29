"""Simplified conversation state for LangGraph workflow."""

from typing import Annotated, Optional, Dict, Any, List
from typing_extensions import TypedDict
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class ConversationState(TypedDict):
    """State object for TeleCorp customer support workflow with ReWOO pattern."""

    # Core LangGraph pattern - messages are the primary state
    messages: Annotated[list[BaseMessage], add_messages]

    # Simple context tracking
    user_id: Optional[str]
    session_id: Optional[str]

    # Persona routing state
    conversation_type: str  # "general", "sales", "support", "billing"
    current_persona: str    # "support", "sales", "billing"
    route_to: Optional[str] # Target agent for routing

    # Plan-and-Execute state
    plan: Optional[List[str]]     # List of planned steps
    current_step: Optional[int]   # Current step being executed
    step_results: Optional[Dict[int, str]]  # Results from each step execution
    plan_complete: Optional[bool] # Whether the plan is fully executed

    # Minimal metadata
    metadata: Dict[str, Any]