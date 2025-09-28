"""Context router node for determining conversation flow."""

import time
from typing import Dict, Any
from langsmith import traceable

from ..state.conversation_state import ConversationState


@traceable(
    name="context_router",
    tags=["routing", "context", "telecorp"],
    metadata={"component": "conversation_routing", "version": "1.0"}
)
def context_router_node(state: ConversationState) -> Dict[str, Any]:
    """
    Route conversation based on available context (ticket vs direct chat).

    Routing Logic:
    1. If ticket_id provided -> "ticket_lookup"
    2. If user_id provided -> "direct_chat"
    3. Default -> "direct_chat"
    """
    start_time = time.time()

    ticket_id = state.get("ticket_id")
    user_id = state.get("user_id")

    # Determine routing decision
    if ticket_id:
        route_decision = "ticket_lookup"
        session_key = f"ticket_{ticket_id}"
    elif user_id:
        route_decision = "direct_chat"
        session_key = f"user_{user_id}"
    else:
        route_decision = "direct_chat"
        session_key = "session_default"

    processing_time = time.time() - start_time

    return {
        "route_decision": route_decision,
        "session_key": session_key,
        "workflow_step": "context_routed",
        "processing_time": processing_time,
        "metadata": {
            **state.get("metadata", {}),
            "routing_time": processing_time,
            "route_taken": route_decision
        }
    }