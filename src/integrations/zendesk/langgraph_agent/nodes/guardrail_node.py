"""LLM-based guardrail node following LangGraph patterns."""

import asyncio
from langchain_core.messages import HumanMessage, AIMessage

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.guardrails.llm_validator import LLMGuardrailValidator
from src.integrations.zendesk.langgraph_agent.guardrails.input_validator import ThreatLevel


async def guardrail_node(state: ConversationState) -> ConversationState:
    """
    LLM-based guardrail validation using intelligent prompt-based security.

    This follows LangGraph best practices:
    - Simple, focused responsibility
    - Works with messages directly
    - Returns updated state
    - Uses sophisticated LLM-based validation instead of simple keywords
    """
    messages = state["messages"]

    # Get the last human message if it exists
    last_human_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_message = msg
            break

    if not last_human_message:
        return state

    # Use LLM-based validation
    try:
        validator = LLMGuardrailValidator()
        threat_level, violation_type, security_message = await validator.validate_input(last_human_message.content)

        # If blocked, return security message and end conversation
        if threat_level == ThreatLevel.BLOCKED:
            return {
                **state,
                "messages": messages + [AIMessage(content=security_message)]
            }

    except Exception as e:
        # If LLM validation fails, fall back to safe (fail-open)
        print(f"Guardrail validation error: {e}")

    # If content is safe or validation failed, continue to normal processing
    return state