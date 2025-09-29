"""Simplified TeleCorp customer support LangGraph workflow."""

import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.nodes.guardrail_node import guardrail_node
from src.integrations.zendesk.langgraph_agent.nodes.conversation_router import conversation_router_node
from src.integrations.zendesk.langgraph_agent.nodes.general_agent import general_agent_node
from src.integrations.zendesk.langgraph_agent.nodes.sales_agent import sales_agent_node
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config

# Set up LangSmith tracing
os.environ.setdefault("LANGCHAIN_TRACING_V2", telecorp_config.LANGCHAIN_TRACING_V2)
if telecorp_config.LANGCHAIN_API_KEY:
    os.environ.setdefault("LANGCHAIN_API_KEY", telecorp_config.LANGCHAIN_API_KEY)
os.environ.setdefault("LANGCHAIN_PROJECT", telecorp_config.LANGCHAIN_PROJECT)
os.environ.setdefault("LANGSMITH_ENDPOINT", telecorp_config.LANGSMITH_ENDPOINT)


def should_continue_after_guardrail(state: ConversationState) -> str:
    """Check if guardrail blocked the request."""
    messages = state["messages"]
    if not messages:
        return "router"

    last_message = messages[-1]

    # If the last message is from AI and contains safety language, we're done
    if (isinstance(last_message, AIMessage) and
        "maintain consistent professional standards" in last_message.content):
        return END

    return "router"


def should_continue_after_router(state: ConversationState) -> str:
    """Route to appropriate agent based on conversation type."""
    conversation_type = state.get("conversation_type", "general")

    if conversation_type == "sales":
        return "sales_agent"
    else:
        return "general_agent"


def should_continue_after_agent(state: ConversationState) -> str:
    """Check if agent wants to use tools."""
    messages = state["messages"]
    last_message = messages[-1]

    # If the last message has tool calls, execute them
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    # Otherwise we're done
    return END


def create_telecorp_graph():
    """
    Create a simple, clean TeleCorp customer support workflow.

    Following LangGraph best practices:
    1. Simple flow with tool integration
    2. Message-based state management
    3. Clear, focused responsibilities for each node
    """

    graph = StateGraph(ConversationState)

    # Add all nodes
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("router", conversation_router_node)
    graph.add_node("general_agent", general_agent_node)
    graph.add_node("sales_agent", sales_agent_node)
    graph.add_node("tools", ToolNode(telecorp_tools))

    # Set entry point
    graph.set_entry_point("guardrail")

    # Add conditional routing
    graph.add_conditional_edges(
        "guardrail",
        should_continue_after_guardrail,
        {
            "router": "router",
            END: END
        }
    )

    graph.add_conditional_edges(
        "router",
        should_continue_after_router,
        {
            "general_agent": "general_agent",
            "sales_agent": "sales_agent"
        }
    )

    # Both agents can use tools
    graph.add_conditional_edges(
        "general_agent",
        should_continue_after_agent,
        {
            "tools": "tools",
            END: END
        }
    )

    graph.add_conditional_edges(
        "sales_agent",
        should_continue_after_agent,
        {
            "tools": "tools",
            END: END
        }
    )

    # After tools, route back based on current persona
    def route_after_tools(state: ConversationState) -> str:
        current_persona = state.get("current_persona", "general_alex")
        if current_persona == "sales_alex":
            return "sales_agent"
        else:
            return "general_agent"

    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "general_agent": "general_agent",
            "sales_agent": "sales_agent"
        }
    )

    # Compile and return
    return graph.compile()