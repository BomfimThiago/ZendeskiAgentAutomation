"""Main TeleCorp customer support LangGraph workflow."""

import os
from langgraph.graph import StateGraph, END
from typing import Literal

from ..state.conversation_state import ConversationState
from ..nodes.security_guard import security_guard_node
from ..nodes.context_router import context_router_node
from ..nodes.telecorp_agent import telecorp_agent_node
from ..nodes.response_filter import response_filter_node
from ..config.langgraph_config import telecorp_config

# Set up LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = telecorp_config.LANGCHAIN_TRACING_V2
if telecorp_config.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = telecorp_config.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = telecorp_config.LANGCHAIN_PROJECT
os.environ["LANGSMITH_ENDPOINT"] = telecorp_config.LANGSMITH_ENDPOINT


def should_continue_after_security(state: ConversationState) -> Literal["context_router", "end"]:
    """Conditional routing after security check."""
    if state.get("is_secure", False):
        return "context_router"
    else:
        return "end"


def should_continue_after_routing(state: ConversationState) -> Literal["telecorp_agent", "end"]:
    """Conditional routing after context routing."""
    # For now, always continue to TeleCorp agent
    # In future, this could route to ticket lookup or other specialized nodes
    return "telecorp_agent"


def create_telecorp_graph() -> StateGraph:
    """
    Create the main TeleCorp customer support workflow graph.

    Workflow:
    1. Security Guard - Validate input for threats
    2. Context Router - Determine conversation type
    3. TeleCorp Agent - Process with LLM
    4. Response Filter - Validate output
    """

    # Create the state graph
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("security_guard", security_guard_node)
    graph.add_node("context_router", context_router_node)
    graph.add_node("telecorp_agent", telecorp_agent_node)
    graph.add_node("response_filter", response_filter_node)

    # Set entry point
    graph.set_entry_point("security_guard")

    # Add edges with conditional logic
    graph.add_conditional_edges(
        "security_guard",
        should_continue_after_security,
        {
            "context_router": "context_router",
            "end": END
        }
    )

    graph.add_conditional_edges(
        "context_router",
        should_continue_after_routing,
        {
            "telecorp_agent": "telecorp_agent",
            "end": END
        }
    )

    # Linear flow after LLM processing
    graph.add_edge("telecorp_agent", "response_filter")
    graph.add_edge("response_filter", END)

    # Compile the graph
    return graph.compile()