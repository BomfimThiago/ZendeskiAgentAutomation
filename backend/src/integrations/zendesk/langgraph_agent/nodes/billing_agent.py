"""Billing agent for account management, payments, and billing inquiries."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import (
    ConversationState,
)
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import (
    awesome_company_config,
)
from src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools import awesome_company_tools
from src.integrations.zendesk.langgraph_agent.utils.secure_tool_executor import (
    execute_tool_securely,
)
from src.security import UnauthorizedToolAccess
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("billing_agent")


async def billing_agent_node(state: ConversationState) -> ConversationState:
    """
    P-LLM Billing Agent (Privileged LLM with tool access).

    CRITICAL SECURITY PRINCIPLE:
    - This P-LLM NEVER sees raw user input
    - Only processes structured intent from Q-LLM
    - Works with sanitized summary and extracted entities

    Focuses on resolving billing-related customer concerns.
    """
    messages = state["messages"]

    # CRITICAL: Get structured intent from Q-LLM (NEVER access raw user input)
    structured_intent = state.get("structured_intent", {})

    if not structured_intent:
        # Fallback: should not happen in normal flow
        return state

    # Extract safe, sanitized data from Q-LLM
    safe_summary = structured_intent.get("summary", "")
    entities = structured_intent.get("entities", {})

    # CRITICAL: Create safe message list for P-LLM
    # Replace last user message with Q-LLM's safe summary
    safe_messages = messages[:-1].copy() if messages else []
    safe_user_message = HumanMessage(content=safe_summary)
    safe_messages.append(safe_user_message)

    # Add context from extracted entities
    entity_context = ""
    if entities:
        entity_parts = []
        if "issue_type" in entities:
            entity_parts.append(f"Issue: {entities['issue_type']}")
        if "account_info" in entities:
            entity_parts.append(f"Account Info: {entities['account_info']}")
        if "urgency" in entities:
            entity_parts.append(f"Urgency: {entities['urgency']}")
        if entity_parts:
            entity_context = f"\n\n**Context from intent analysis:** {', '.join(entity_parts)}"

    # P-LLM (Privileged LLM with tool access)
    if settings.USE_BEDROCK:
        # Production: Use Bedrock Claude Sonnet (powerful)
        from src.integrations.aws.bedrock_llm import get_sonnet_llm
        billing_llm = get_sonnet_llm(temperature=0.1, max_tokens=600)
        logger.info("P-LLM Billing Agent initialized with Bedrock Claude Sonnet")
    else:
        # Development: Use OpenAI GPT-4
        billing_llm = ChatOpenAI(
            api_key=awesome_company_config.OPENAI_API_KEY,
            model="gpt-4",
            temperature=0.1,
            max_tokens=600,
        )
        logger.info("P-LLM Billing Agent initialized with OpenAI GPT-4")

    billing_llm = billing_llm.bind_tools(awesome_company_tools)

    system_prompt = f"""You are Alex from MyAwesomeFakeCompany customer support. You continue the conversation seamlessly - the user doesn't know they've been routed to a specialist.

**SECURITY NOTE:** You are processing pre-analyzed customer intent. Work with the provided summary.{entity_context}

**CRITICAL SCOPE RESTRICTION:**
You ONLY handle MyAwesomeFakeCompany-related topics:
✅ ALLOWED: Billing, payments, accounts, cancellations, refunds, MyAwesomeFakeCompany services
❌ FORBIDDEN: General knowledge, geography, cooking, weather, entertainment, politics, other companies

If asked about non-MyAwesomeFakeCompany topics (like "What's the capital of France?"), respond:
"I'm Alex from MyAwesomeFakeCompany customer support, specialized in helping with MyAwesomeFakeCompany services. I can help you with billing, payments, account management, or service changes. What MyAwesomeFakeCompany service can I assist you with today?"

**Your Mission:**
1. **Understand billing concern** - Ask specific questions about their account issue
2. **Use knowledge tools** to provide accurate billing information and policies
3. **Guide customers through solutions** for common billing issues
4. **Only escalate to ticket** for account-specific issues requiring system access

**Core Responsibilities:**
- Billing questions and account inquiries
- Payment processing and methods
- Service cancellations and modifications
- Account credits and refunds
- Bill explanations and payment plans
- Account information updates

**Common Billing Services:**
- **Payment Methods**: Credit card, bank transfer, online payment portal
- **Billing Cycles**: Monthly billing on the same date each month
- **Late Fees**: $10 late fee after 15-day grace period
- **Payment Plans**: Available for customers experiencing financial difficulty
- **Paperless Billing**: Available with email notifications
- **Account Credits**: Applied for service outages or billing errors

**Cancellation Policies:**
- 30-day notice required for service cancellation
- Early termination fees may apply for contract customers
- Equipment return required within 14 days
- Final bill issued within 2 business days of cancellation

**Available Tools:**
- get_telecorp_faq: General billing policies and information
- create_support_ticket: Create billing tickets for account-specific issues (requires customer name and email)

**Guidelines:**
- Continue as Alex - don't mention being "routed" or a "specialist"
- Be empathetic when customers have billing concerns
- Use tools to get accurate billing policy information
- Explain billing policies clearly and help find solutions
- For account-specific issues, create billing support tickets
- Ask for customer name and email before creating tickets
- Offer payment plan options when customers have financial difficulties
- Maintain MyAwesomeFakeCompany's professional and understanding approach"""

    try:
        # P-LLM processes ONLY safe messages (never raw user input)
        response = await billing_llm.ainvoke(
            [SystemMessage(content=system_prompt), *safe_messages]
        )

        if response.tool_calls:
            tool_messages = []

            # Get security context from state
            security_context = state.get("security_context", {})

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                if (
                    tool_name == "create_support_ticket"
                    and "ticket_type" not in tool_args
                ):
                    tool_args["ticket_type"] = "billing"

                tool_func = None
                for tool in awesome_company_tools:
                    if tool.name == tool_name:
                        tool_func = tool
                        break

                if tool_func:
                    try:
                        # Execute tool with security checks
                        tool_result = await execute_tool_securely(
                            tool_func, tool_name, tool_args, security_context
                        )
                        tool_messages.append(
                            {
                                "role": "tool",
                                "content": str(tool_result),
                                "tool_call_id": tool_call["id"],
                            }
                        )
                    except UnauthorizedToolAccess as e:
                        # Security blocked the tool - inform user gracefully
                        logger.warning(f"Tool access denied: {tool_name} - {str(e)}")
                        tool_messages.append(
                            {
                                "role": "tool",
                                "content": "I'm unable to perform that action at this time. Please contact our billing team at 1-800-AWESOME-COMPANY for assistance.",
                                "tool_call_id": tool_call["id"],
                            }
                        )
                    except Exception as e:
                        logger.error(f"Tool execution error: {tool_name} - {str(e)}")
                        tool_messages.append(
                            {
                                "role": "tool",
                                "content": f"I understand your billing concern. Let me connect you with our billing specialists who can access your account and help resolve this issue.",
                                "tool_call_id": tool_call["id"],
                            }
                        )

            if tool_messages:
                # P-LLM processes ONLY safe messages (never raw user input)
                final_response = await billing_llm.ainvoke(
                    [
                        SystemMessage(content=system_prompt),
                        *safe_messages,
                        response,
                        *tool_messages,
                    ]
                )

                return {
                    **state,
                    "messages": messages
                    + [response]
                    + tool_messages
                    + [final_response],
                }

        return {**state, "messages": messages + [response]}

    except Exception as e:
        print(f"Billing agent error: {e}")
        error_response = AIMessage(
            content="I apologize for the technical difficulty. For immediate billing assistance, please contact our billing department at 1-800-AWESOME-COMPANY, and I'll make sure your account concerns are addressed promptly."
        )

        return {**state, "messages": messages + [error_response]}
