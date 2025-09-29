"""Sales agent node following LangGraph patterns."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.integrations.zendesk.langgraph_agent.prompts.persona import SALES_ALEX_PERSONA
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools


async def sales_agent_node(state: ConversationState) -> ConversationState:
    """
    Sales-focused agent using LangGraph patterns.

    Handles:
    - Plans and pricing inquiries
    - Sales consultations
    - Product recommendations
    - Closing sales and next steps
    """
    messages = state["messages"]

    # Add system message for sales persona, preserving conversation context
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=SALES_ALEX_PERSONA)] + messages
    else:
        # Replace existing system message with sales persona while preserving conversation
        new_messages = [SystemMessage(content=SALES_ALEX_PERSONA)]
        new_messages.extend([msg for msg in messages if not isinstance(msg, SystemMessage)])
        messages = new_messages

    # Initialize LLM with all tools (especially pricing)
    llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model=telecorp_config.DEFAULT_MODEL,
        temperature=telecorp_config.TEMPERATURE,
        max_tokens=telecorp_config.MAX_TOKENS
    ).bind_tools(telecorp_tools)

    try:
        response = await llm.ainvoke(messages)

        return {
            **state,
            "messages": messages + [response]
        }

    except Exception as e:
        error_message = "I apologize, but I'm experiencing technical difficulties. Please contact our sales team directly at 1-800-NEW-PLAN and they'll help you find the perfect plan!"

        return {
            **state,
            "messages": messages + [AIMessage(content=error_message)],
            "metadata": {
                **state.get("metadata", {}),
                "error": str(e)
            }
        }