"""Billing agent for account management, payments, and billing inquiries."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools


async def billing_agent_node(state: ConversationState) -> ConversationState:
    """
    Billing agent that handles account management, payments, cancellations, and billing issues.

    Focuses on resolving billing-related customer concerns.
    """
    messages = state["messages"]

    # Create billing agent with tools
    billing_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-4",
        temperature=0.1,
        max_tokens=600
    ).bind_tools(telecorp_tools)

    system_prompt = """You are Alex from TeleCorp customer support. You continue the conversation seamlessly - the user doesn't know they've been routed to a specialist.

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
- Maintain TeleCorp's professional and understanding approach"""

    try:
        # Get response from billing agent
        response = await billing_llm.ainvoke([
            SystemMessage(content=system_prompt),
            *messages
        ])

        # Handle tool calls if any
        if response.tool_calls:
            tool_messages = []

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Add context for billing tickets
                if tool_name == "create_support_ticket" and "ticket_type" not in tool_args:
                    tool_args["ticket_type"] = "billing"

                # Find and execute the tool
                tool_func = None
                for tool in telecorp_tools:
                    if tool.name == tool_name:
                        tool_func = tool
                        break

                if tool_func:
                    try:
                        tool_result = tool_func.invoke(tool_args)
                        tool_messages.append({
                            "role": "tool",
                            "content": str(tool_result),
                            "tool_call_id": tool_call["id"]
                        })
                    except Exception as e:
                        tool_messages.append({
                            "role": "tool",
                            "content": f"I understand your billing concern. Let me connect you with our billing specialists who can access your account and help resolve this issue.",
                            "tool_call_id": tool_call["id"]
                        })

            # Get final response after tool execution
            if tool_messages:
                final_response = await billing_llm.ainvoke([
                    SystemMessage(content=system_prompt),
                    *messages,
                    response,
                    *tool_messages
                ])

                return {
                    **state,
                    "messages": messages + [response] + tool_messages + [final_response]
                }

        # No tools used - direct response
        return {
            **state,
            "messages": messages + [response]
        }

    except Exception as e:
        print(f"Billing agent error: {e}")
        # Fallback response
        error_response = AIMessage(
            content="I apologize for the technical difficulty. For immediate billing assistance, please contact our billing department at 1-800-TELECORP, and I'll make sure your account concerns are addressed promptly."
        )

        return {
            **state,
            "messages": messages + [error_response]
        }