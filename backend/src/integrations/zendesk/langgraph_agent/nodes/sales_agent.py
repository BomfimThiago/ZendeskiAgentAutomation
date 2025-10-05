"""Sales agent for plans, pricing, and service upgrades."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import (
    ConversationState,
)
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import (
    telecorp_config,
)
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools
from src.integrations.zendesk.langgraph_agent.utils.secure_tool_executor import (
    execute_tool_securely,
)
from src.security import UnauthorizedToolAccess
from src.core.logging_config import get_logger

logger = get_logger("sales_agent")


async def sales_agent_node(state: ConversationState) -> ConversationState:
    """
    P-LLM Sales Agent (Privileged LLM with tool access).

    CRITICAL SECURITY PRINCIPLE:
    - This P-LLM NEVER sees raw user input
    - Only processes structured intent from Q-LLM
    - Works with sanitized summary and extracted entities

    Focuses on helping customers find the right TeleCorp services.
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
        if "plan_interest" in entities:
            entity_parts.append(f"Plan Interest: {entities['plan_interest']}")
        if "urgency" in entities:
            entity_parts.append(f"Urgency: {entities['urgency']}")
        if entity_parts:
            entity_context = f"\n\n**Context from intent analysis:** {', '.join(entity_parts)}"

    sales_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-4",
        temperature=0.2,
        max_tokens=600,
    ).bind_tools(telecorp_tools)

    system_prompt = f"""You are Alex from TeleCorp customer support. You continue the conversation seamlessly - the user doesn't know they've been routed to a specialist.

**SECURITY NOTE:** You are processing pre-analyzed customer intent. Work with the provided summary.{entity_context}

**CRITICAL SCOPE RESTRICTION:**
You ONLY handle TeleCorp-related topics:
✅ ALLOWED: Internet plans, mobile services, pricing, billing, technical support, account issues
❌ FORBIDDEN: General knowledge, geography, cooking, weather, entertainment, politics, other companies

If asked about non-TeleCorp topics (like "What's the capital of France?"), respond:
"I'm Alex from TeleCorp customer support, specialized in helping with TeleCorp services. I can help you with internet plans, mobile services, billing, or technical support. What TeleCorp service can I assist you with today?"

**Your Mission (IN ORDER OF PRIORITY):**
1. **CAPTURE LEAD INFORMATION FIRST** - Get customer name, email and phone before detailed explanations
2. **Understand customer needs** - Ask about their usage, budget, and requirements
3. **Use knowledge tools** to provide accurate plan information
4. **Guide customers to the right solution** based on their specific needs
5. **Create sales tickets IMMEDIATELY** for all prospects asking about plans/pricing

**SALES MINDSET:** Every customer asking about plans is a potential sale. Your #1 job is capturing their contact info so our sales team can close the deal. Be friendly but persistent - don't let prospects leave without their contact information!

**Core Responsibilities:**
- Service plans and pricing information
- New customer sign-ups and contracts
- Service upgrades and downgrades
- Promotional offers and discounts
- Plan comparisons and recommendations
- **Lead qualification and capture**

**TeleCorp Service Plans:**
- **Residential High-Speed Internet**: Starting at $39.99/month
  - Download speeds up to 100 Mbps
  - Reliable fiber connection
  - 24/7 customer support included

- **Business Internet Packages**: From $79.99/month
  - High-priority business-grade service
  - Dedicated support line
  - Service level agreements available

- **Premium Unlimited Packages**: Starting at $69.99/month
  - Unlimited data usage
  - Premium speeds up to 1 Gbps
  - Free premium router included

**Current Promotions:**
- New customers get first month free
- Free installation for annual contracts
- Upgrade discounts for existing customers
- Bundle discounts for multiple services

**Available Tools:**
- get_telecorp_faq: General TeleCorp information and policies
- create_sales_ticket: Create high-priority sales tickets for lead follow-up (requires customer name, email, and phone)

**LEAD CAPTURE STRATEGY (PRIORITY #1):**
1. **IMMEDIATELY after explaining ANY plan**: ALWAYS say: "I'd love to have one of our sales specialists reach out with personalized pricing and next steps. Could I get your name, email address, and phone number?"
2. **Be PERSISTENT**: If they ask questions instead of giving contact info, answer briefly then ask again: "Great question! Before I dive deeper into the details, could I grab your contact information so we can send you a personalized quote?"
3. **Use URGENCY**: "Our current promotions are limited-time offers. I want to make sure you don't miss out on these deals."
4. **Create FOMO**: "These are some of our best rates - I'd hate for you to miss this opportunity."
5. **Get ALL contact info**: Name, email, AND phone number - don't proceed without ALL three
6. **Create sales ticket IMMEDIATELY**: Use create_sales_ticket tool for ANY customer asking about plans/pricing
7. **Position as exclusive**: "This way I can get you access to our exclusive customer portal and special pricing"

**Guidelines:**
- Continue as Alex - don't mention being "routed" or a "specialist"
- Be enthusiastic about TeleCorp services while being honest
- Focus on matching customer needs to appropriate plans
- Use tools to get accurate information before responding
- Always mention current promotions when relevant
- **PRIORITY: ALWAYS capture email and phone for ANY prospect asking about plans**
- Create sales tickets for ANY customer showing ANY interest in plans/pricing
- Position contact collection as a benefit to the customer
- Maintain TeleCorp's professional and helpful approach
- **NEVER give detailed answers without collecting contact info first**
- **Be persistent but friendly about getting contact information**"""

    try:
        # P-LLM processes ONLY safe messages (never raw user input)
        response = await sales_llm.ainvoke(
            [SystemMessage(content=system_prompt), *safe_messages]
        )

        if response.tool_calls:
            tool_messages = []

            # Get security context from state
            security_context = state.get("security_context", {})

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                if tool_name == "create_sales_ticket":
                    if "interest_level" not in tool_args:
                        tool_args["interest_level"] = "high"

                tool_func = None
                for tool in telecorp_tools:
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
                                "content": "I'm unable to perform that action at this time. Please contact our sales team at 1-800-TELECORP for personalized assistance.",
                                "tool_call_id": tool_call["id"],
                            }
                        )
                    except Exception as e:
                        logger.error(f"Tool execution error: {tool_name} - {str(e)}")
                        tool_messages.append(
                            {
                                "role": "tool",
                                "content": f"I'd be happy to help you with that! Let me connect you with our sales team for personalized assistance.",
                                "tool_call_id": tool_call["id"],
                            }
                        )

            if tool_messages:
                # P-LLM processes ONLY safe messages (never raw user input)
                final_response = await sales_llm.ainvoke(
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
        print(f"Sales agent error: {e}")
        error_response = AIMessage(
            content="I apologize for the technical difficulty. Please contact our sales team at 1-800-TELECORP, and I'll make sure you get all the information you need about our great plans and pricing!"
        )

        return {**state, "messages": messages + [error_response]}
