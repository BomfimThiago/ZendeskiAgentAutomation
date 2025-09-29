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

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.nodes.conversation_router import supervisor_agent_node
from src.integrations.zendesk.langgraph_agent.nodes.support_agent import support_agent_node
from src.integrations.zendesk.langgraph_agent.nodes.sales_agent import sales_agent_node
from src.integrations.zendesk.langgraph_agent.nodes.billing_agent import billing_agent_node
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.core.config import settings

# Create LangSmith client using core settings
langsmith_client = None
if settings.LANGSMITH_API_KEY and settings.LANGSMITH_TRACING:
    langsmith_client = Client(
        api_key=settings.LANGSMITH_API_KEY,
        api_url=settings.LANGSMITH_ENDPOINT or "https://api.smith.langchain.com"
    )





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
        # No routing needed - supervisor handled the conversation
        return END


def create_telecorp_graph():
    """
    Create TeleCorp customer support workflow with supervisor routing pattern.

    Following LangGraph best practices:
    1. Supervisor analyzes customer needs and routes to appropriate agent
    2. Each agent specializes in their domain (support, sales, billing)
    3. Plan-and-execute pattern handled by individual agents
    4. Message-based state management with session persistence
    """

    graph = StateGraph(ConversationState)

    # Add all nodes
    graph.add_node("supervisor", supervisor_agent_node)
    graph.add_node("support_agent", support_agent_node)
    graph.add_node("sales_agent", sales_agent_node)
    graph.add_node("billing_agent", billing_agent_node)

    # Set supervisor as entry point - Alex greets and routes customers
    graph.set_entry_point("supervisor")

    # Supervisor routes to appropriate agent based on customer needs
    graph.add_conditional_edges(
        "supervisor",
        should_continue_after_supervisor,
        {
            "support_agent": "support_agent",
            "sales_agent": "sales_agent",
            "billing_agent": "billing_agent",
            END: END
        }
    )

    # All agents return to END after handling the customer
    graph.add_edge("support_agent", END)
    graph.add_edge("sales_agent", END)
    graph.add_edge("billing_agent", END)

    # Compile with checkpointer for state persistence
    checkpointer = MemorySaver()
    compiled_graph = graph.compile(checkpointer=checkpointer)

    # Wrap graph execution with LangSmith tracing if configured
    if langsmith_client and settings.LANGSMITH_TRACING:
        class TracedGraph:
            def __init__(self, graph, client, project):
                self.graph = graph
                self.client = client
                self.project = project

            async def ainvoke(self, input_data, config=None):
                with tracing_context(
                    enabled=True,
                    project_name=self.project,
                    langsmith_extra={"client": self.client}
                ):
                    return await self.graph.ainvoke(input_data, config)

            def invoke(self, input_data, config=None):
                with tracing_context(
                    enabled=True,
                    project_name=self.project,
                    langsmith_extra={"client": self.client}
                ):
                    return self.graph.invoke(input_data, config)

        return TracedGraph(compiled_graph, langsmith_client, settings.LANGSMITH_PROJECT)

    return compiled_graph