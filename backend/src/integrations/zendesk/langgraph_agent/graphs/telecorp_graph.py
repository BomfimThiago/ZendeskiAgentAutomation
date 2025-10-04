"""TeleCorp supervisor-based LangGraph workflow with plan-and-execute pattern."""

import logging
import warnings
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from langsmith import Client
from langsmith.run_helpers import tracing_context

# Suppress LangSmith warnings and errors from appearing in frontend
logging.getLogger("langsmith").setLevel(logging.ERROR)
logging.getLogger("langsmith.client").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")

from src.integrations.zendesk.langgraph_agent.state.conversation_state import (
    ConversationState,
)
from src.integrations.zendesk.langgraph_agent.nodes.conversation_router import (
    supervisor_agent_node,
)
from src.integrations.zendesk.langgraph_agent.nodes.support_agent import (
    support_agent_node,
)
from src.integrations.zendesk.langgraph_agent.nodes.sales_agent import sales_agent_node
from src.integrations.zendesk.langgraph_agent.nodes.billing_agent import (
    billing_agent_node,
)
from src.integrations.zendesk.langgraph_agent.nodes.guardrail_node import (
    input_validation_node,
    output_sanitization_node,
    should_continue_after_validation,
)
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import (
    telecorp_config,
)
from src.core.config import settings, setup_langsmith

setup_langsmith()

langsmith_client = None

api_key = settings.LANGCHAIN_API_KEY or settings.LANGSMITH_API_KEY
tracing_enabled = settings.LANGCHAIN_TRACING_V2 or settings.LANGSMITH_TRACING

if api_key and tracing_enabled:
    endpoint = (
        settings.LANGCHAIN_ENDPOINT
        or settings.LANGSMITH_ENDPOINT
        or "https://api.smith.langchain.com"
    )
    langsmith_client = Client(api_key=api_key, api_url=endpoint)


def should_continue_after_supervisor(state: ConversationState) -> str:
    """Route from supervisor to appropriate agent or end conversation."""
    route_to = state.get("route_to")

    if route_to == "support":
        return "support_agent"
    elif route_to == "sales":
        return "sales_agent"
    elif route_to == "billing":
        return "billing_agent"
    else:
        return END


def create_telecorp_graph():
    """
    Create TeleCorp customer support workflow with supervisor routing pattern.

    Following LangGraph best practices:
    1. Input validation to prevent prompt injection and out-of-scope queries
    2. Supervisor analyzes customer needs and routes to appropriate agent
    3. Each agent specializes in their domain (support, sales, billing)
    4. Output sanitization to remove sensitive information
    5. Message-based state management with session persistence
    """

    graph = StateGraph(ConversationState)

    graph.add_node("input_validation", input_validation_node)
    graph.add_node("supervisor", supervisor_agent_node)
    graph.add_node("support_agent", support_agent_node)
    graph.add_node("sales_agent", sales_agent_node)
    graph.add_node("billing_agent", billing_agent_node)
    graph.add_node("output_sanitization", output_sanitization_node)

    graph.set_entry_point("input_validation")

    graph.add_conditional_edges(
        "input_validation",
        should_continue_after_validation,
        {"supervisor": "supervisor", "sanitize": "output_sanitization"},
    )

    graph.add_conditional_edges(
        "supervisor",
        should_continue_after_supervisor,
        {
            "support_agent": "support_agent",
            "sales_agent": "sales_agent",
            "billing_agent": "billing_agent",
            END: "output_sanitization",
        },
    )

    graph.add_edge("support_agent", "output_sanitization")
    graph.add_edge("sales_agent", "output_sanitization")
    graph.add_edge("billing_agent", "output_sanitization")
    graph.add_edge("output_sanitization", END)

    checkpointer = MemorySaver()
    compiled_graph = graph.compile(checkpointer=checkpointer)

    if langsmith_client and tracing_enabled:

        class TracedGraph:
            def __init__(self, graph, client, project):
                self.graph = graph
                self.client = client
                self.project = project

            async def ainvoke(self, input_data, config=None):
                with tracing_context(
                    enabled=True,
                    project_name=self.project,
                    langsmith_extra={"client": self.client},
                ):
                    return await self.graph.ainvoke(input_data, config)

            def invoke(self, input_data, config=None):
                with tracing_context(
                    enabled=True,
                    project_name=self.project,
                    langsmith_extra={"client": self.client},
                ):
                    return self.graph.invoke(input_data, config)

        project_name = (
            settings.LANGCHAIN_PROJECT
            or settings.LANGSMITH_PROJECT
            or "telecorp-agent-automation"
        )
        return TracedGraph(compiled_graph, langsmith_client, project_name)

    return compiled_graph
