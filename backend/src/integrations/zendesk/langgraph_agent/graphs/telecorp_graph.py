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
from src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent import (
    quarantined_agent_node,
)
from src.integrations.zendesk.langgraph_agent.nodes.intent_extraction_node import (
    intent_extraction_node,
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


def should_continue_after_intent_extraction(state: ConversationState) -> str:
    """
    Route after Q-LLM intent extraction (True Dual LLM Pattern).

    Routes:
    - If blocked (attack detected) → output_sanitization (already has response)
    - If suspicious but not blocked → quarantined_agent (Q-LLM, no tools)
    - If safe → supervisor (P-LLM with tools)

    This ensures ALL user input is processed by Q-LLM first,
    and P-LLM NEVER sees raw user input.
    """
    # If blocked by Q-LLM, go directly to output sanitization
    if state.get("security_blocked", False):
        return "sanitize"

    # Get structured intent from Q-LLM
    structured_intent = state.get("structured_intent", {})
    safety_assessment = structured_intent.get("safety_assessment", "suspicious")
    intent = structured_intent.get("intent", "general")

    # If Q-LLM marked as attack, route to quarantined agent
    if intent == "attack" or safety_assessment == "attack":
        return "quarantined"

    # If suspicious, route to quarantined agent (no tools)
    if safety_assessment == "suspicious":
        return "quarantined"

    # Safe input → route to P-LLM supervisor
    # P-LLM will ONLY see structured intent, never raw user input
    return "supervisor"


def create_telecorp_graph():
    """
    Create TeleCorp customer support workflow with TRUE Dual-LLM pattern.

    Implements Simon Willison's dual-LLM security architecture:
    1. Q-LLM (intent extraction) processes ALL raw user input FIRST
    2. Q-LLM extracts structured intent (no tools, limited damage)
    3. P-LLM (supervisor + agents) ONLY sees structured intent
    4. P-LLM NEVER sees raw user input
    5. Architectural guarantee (not probabilistic filtering)

    Flow:
    START → Q-LLM Intent Extraction → [Routing Decision] →
      - If attack: Output Sanitization → END
      - If suspicious: Q-LLM Response (no tools) → Output Sanitization → END
      - If safe: P-LLM Supervisor → Agent → Output Sanitization → END
    """

    graph = StateGraph(ConversationState)

    # Add all nodes
    graph.add_node("intent_extraction", intent_extraction_node)  # Q-LLM (ALL input)
    graph.add_node("quarantined_agent", quarantined_agent_node)  # Q-LLM (no tools)
    graph.add_node("supervisor", supervisor_agent_node)  # P-LLM router
    graph.add_node("support_agent", support_agent_node)
    graph.add_node("sales_agent", sales_agent_node)
    graph.add_node("billing_agent", billing_agent_node)
    graph.add_node("output_sanitization", output_sanitization_node)

    # CRITICAL: Entry point is Q-LLM intent extraction
    # ALL user input must go through Q-LLM first
    graph.set_entry_point("intent_extraction")

    # Route from Q-LLM intent extraction
    graph.add_conditional_edges(
        "intent_extraction",
        should_continue_after_intent_extraction,
        {
            "supervisor": "supervisor",  # Safe → P-LLM (sees structured data only)
            "quarantined": "quarantined_agent",  # Suspicious → Q-LLM (no tools)
            "sanitize": "output_sanitization",  # Blocked → Direct to sanitization
        },
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

    # All agents flow to output sanitization
    graph.add_edge("quarantined_agent", "output_sanitization")  # Q-LLM output
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
                # Extract security metadata from state
                metadata = {
                    "security_enabled": True,
                    "dual_llm_architecture": True,
                }

                # Add initial message info
                if "messages" in input_data and input_data["messages"]:
                    last_msg = input_data["messages"][-1]
                    metadata["user_message"] = last_msg.content[:100] if hasattr(last_msg, 'content') else str(last_msg)[:100]

                # Initialize config if not provided
                if config is None:
                    config = {}

                # Add metadata to config for LangSmith
                if "metadata" not in config:
                    config["metadata"] = {}
                config["metadata"].update(metadata)

                # Add tags to config
                if "tags" not in config:
                    config["tags"] = []
                config["tags"].extend(["dual-llm", "security-enabled"])

                # Invoke graph with metadata
                result = await self.graph.ainvoke(input_data, config)

                # Extract final security state from result and log
                if isinstance(result, dict):
                    final_metadata = {
                        # Core security info
                        "trust_level": result.get("trust_level", "UNKNOWN"),
                        "trust_score": result.get("trust_score", 0.0),
                        "security_blocked": result.get("security_blocked", False),
                        "threat_type": result.get("threat_type"),
                        "current_persona": result.get("current_persona", "unknown"),
                        "route_to": result.get("route_to"),

                        # Security context details
                        "security_context_id": result.get("security_context", {}).get("context_id") if result.get("security_context") else None,
                        "security_flags": result.get("security_context", {}).get("security_flags", []) if result.get("security_context") else [],
                        "blocked_reasons": result.get("security_context", {}).get("blocked_reasons", []) if result.get("security_context") else [],
                    }

                    # Log to console for debugging
                    print(f"\n🔒 SECURITY STATE: {final_metadata}")

                return result

            def invoke(self, input_data, config=None):
                metadata = {
                    "security_enabled": True,
                    "dual_llm_architecture": True,
                }

                if "messages" in input_data and input_data["messages"]:
                    last_msg = input_data["messages"][-1]
                    metadata["user_message"] = last_msg.content[:100] if hasattr(last_msg, 'content') else str(last_msg)[:100]

                with tracing_context(
                    enabled=True,
                    project_name=self.project,
                    langsmith_extra={"client": self.client},
                    tags=["dual-llm", "security-enabled"],
                    metadata=metadata,
                ):
                    result = self.graph.invoke(input_data, config)

                    if isinstance(result, dict):
                        final_metadata = {
                            "trust_level": result.get("trust_level", "UNKNOWN"),
                            "trust_score": result.get("trust_score", 0.0),
                            "security_blocked": result.get("security_blocked", False),
                            "threat_type": result.get("threat_type"),
                            "current_persona": result.get("current_persona", "unknown"),
                        }
                        print(f"\n🔒 SECURITY STATE: {final_metadata}")

                    return result

        project_name = (
            settings.LANGCHAIN_PROJECT
            or settings.LANGSMITH_PROJECT
            or "telecorp-agent-automation"
        )
        return TracedGraph(compiled_graph, langsmith_client, project_name)

    return compiled_graph
