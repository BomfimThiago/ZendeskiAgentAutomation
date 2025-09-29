"""General support agent node following LangGraph patterns."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.integrations.zendesk.langgraph_agent.prompts.persona import GENERAL_ALEX_PERSONA
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools


async def general_agent_node(state: ConversationState) -> ConversationState:
    """
    General customer support agent using LangGraph patterns.

    Handles:
    - Initial greetings and general inquiries
    - Company information requests
    - Basic support questions
    - Routes to sales when appropriate
    """
    messages = state["messages"]

    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=GENERAL_ALEX_PERSONA)] + messages
    else:
        new_messages = [SystemMessage(content=GENERAL_ALEX_PERSONA)]
        new_messages.extend([msg for msg in messages if not isinstance(msg, SystemMessage)])
        messages = new_messages

    llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model=telecorp_config.DEFAULT_MODEL,
        temperature=telecorp_config.TEMPERATURE,
        max_tokens=telecorp_config.MAX_TOKENS
    ).bind_tools([
        tool for tool in telecorp_tools
        if tool.name in ["get_telecorp_company_info", "get_telecorp_faq"]
    ])

    try:
        response = await llm.ainvoke(messages)

        return {
            **state,
            "messages": messages + [response]
        }

    except Exception as e:
        error_message = "I apologize, but I'm experiencing technical difficulties. Please try again or contact TeleCorp support at 1-800-TELECORP."

        return {
            **state,
            "messages": messages + [AIMessage(content=error_message)],
            "metadata": {
                **state.get("metadata", {}),
                "error": str(e)
            }
        }