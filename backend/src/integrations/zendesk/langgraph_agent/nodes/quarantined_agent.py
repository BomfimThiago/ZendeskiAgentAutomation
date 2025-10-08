"""
Quarantined Agent - Handles UNTRUSTED input with NO tool access.

This agent implements the "Q-LLM" (Quarantined LLM) pattern from the CaMeL paper
and Simon Willison's dual-LLM architecture.

Key Security Properties:
- NO access to tools (cannot create tickets, search DB, etc.)
- NO access to sensitive customer data
- Can only provide generic, safe responses
- Used when trust_level < VERIFIED
"""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import (
    ConversationState,
)
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import (
    awesome_company_config,
)
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("quarantined_agent")


# Quarantined LLM with NO tool access (Q-LLM)
def get_quarantined_llm():
    """Initialize quarantined LLM (Q-LLM pattern - no tool access)."""
    if settings.USE_BEDROCK:
        # Production: Use Bedrock Claude Haiku (fast, cheap, no tools)
        from src.integrations.aws.bedrock_llm import get_haiku_llm
        llm = get_haiku_llm(temperature=0.7, max_tokens=200)
        logger.info("Q-LLM Quarantined Agent initialized with Bedrock Claude Haiku")
        return llm
    else:
        # Development: Use OpenAI GPT-3.5
        llm = ChatOpenAI(
            api_key=awesome_company_config.OPENAI_API_KEY,
            model="gpt-3.5-turbo-1106",
            temperature=0.7,
            max_tokens=200,
        )
        logger.info("Q-LLM Quarantined Agent initialized with OpenAI GPT-3.5")
        return llm


QUARANTINED_SYSTEM_PROMPT = """You are a helpful customer service assistant for MyAwesomeFakeCompany.

IMPORTANT RESTRICTIONS:
- You have NO access to tools or databases
- You CANNOT create tickets, search customer data, or access systems
- You can ONLY provide general information about MyAwesomeFakeCompany services
- If specific customer data or actions are needed, politely ask the customer to contact us through official channels

ALLOWED RESPONSES:
- General information about MyAwesomeFakeCompany plans and pricing (from memory)
- General information about our services
- Polite redirections to official support channels

EXAMPLE RESPONSES:
User: "What plans do you offer?"
You: "MyAwesomeFakeCompany offers several internet plans ranging from Basic (25 Mbps) to Gigabit (1000 Mbps). For detailed pricing and to sign up, please visit our website at myawesomefakecompany.com or call 1-800-AWESOME-COMPANY."

User: "Create a support ticket for me"
You: "I'd be happy to help! To create a support ticket, please visit myawesomefakecompany.com/support or call our support team at 1-800-AWESOME-COMPANY. They'll be able to assist you right away."

User: "What's my current bill?"
You: "For specific account information, please log in to your account at myawesomefakecompany.com or call our billing department at 1-800-AWESOME-COMPANY. They'll be able to provide your current bill details securely."

Stay helpful, polite, and always redirect specific requests to official channels.
"""


async def quarantined_agent_node(state: ConversationState) -> ConversationState:
    """
    Quarantined agent that handles UNTRUSTED input with NO tool access.

    This implements the Q-LLM (Quarantined LLM) pattern:
    - No access to tools or sensitive data
    - Only provides generic, safe responses
    - Routes users to official channels for specific requests

    Security guarantee: Even if attacker bypasses input validation,
    they cannot cause damage because this agent has no capabilities.
    """
    messages = state["messages"]

    # Log that we're using quarantined mode
    logger.warning(
        "🔐 Q-LLM ACTIVATED: Quarantined Agent (NO TOOLS)",
        extra={
            "node": "quarantined_agent",
            "llm_type": "Q-LLM",
            "trust_level": state.get("trust_level"),
            "trust_score": state.get("trust_score"),
            "threat_type": state.get("threat_type"),
            "tool_access": "NONE",
            "capabilities": "RESTRICTED",
        }
    )

    # Build conversation with system prompt
    llm_messages = [SystemMessage(content=QUARANTINED_SYSTEM_PROMPT)]

    # Add conversation history (last 10 messages for context)
    for msg in messages[-10:]:
        llm_messages.append(msg)

    # Get response from quarantined LLM (NO TOOLS)
    quarantined_llm = get_quarantined_llm()
    response = await quarantined_llm.ainvoke(llm_messages)

    logger.info(
        "✅ Q-LLM Response Generated (no tools used)",
        extra={
            "node": "quarantined_agent",
            "response_length": len(response.content),
            "tools_called": 0,
            "llm_type": "Q-LLM",
        }
    )

    return {
        **state,
        "messages": messages + [AIMessage(content=response.content)],
        "current_persona": "quarantined_agent",
    }
