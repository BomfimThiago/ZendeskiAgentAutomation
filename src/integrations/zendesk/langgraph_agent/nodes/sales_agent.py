"""Sales agent for plans, pricing, and service upgrades."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools


async def sales_agent_node(state: ConversationState) -> ConversationState:
    """
    Sales agent that handles plans, pricing, sign-ups, and service upgrades.

    Focuses on helping customers find the right TeleCorp services.
    """
    messages = state["messages"]

    # Create sales agent with tools
    sales_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-4",
        temperature=0.2,
        max_tokens=600
    ).bind_tools(telecorp_tools)

    system_prompt = """You are Alex from TeleCorp customer support. You continue the conversation seamlessly - the user doesn't know they've been routed to a specialist.

**Your Mission:**
1. **Understand customer needs** - Ask about their usage, budget, and requirements
2. **Use knowledge tools** to provide accurate plan information
3. **Guide customers to the right solution** based on their specific needs
4. **Only escalate to ticket** for complex pricing or special requests

**Core Responsibilities:**
- Service plans and pricing information
- New customer sign-ups and contracts
- Service upgrades and downgrades
- Promotional offers and discounts
- Plan comparisons and recommendations

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
- create_support_ticket: Create sales tickets for complex requests (requires customer name and email)

**Guidelines:**
- Continue as Alex - don't mention being "routed" or a "specialist"
- Be enthusiastic about TeleCorp services while being honest
- Focus on matching customer needs to appropriate plans
- Use tools to get accurate information before responding
- Always mention current promotions when relevant
- Ask for customer details when they're ready to sign up
- Create sales tickets only for complex pricing requests or special deals
- Maintain TeleCorp's professional and helpful approach"""

    try:
        # Get response from sales agent
        response = await sales_llm.ainvoke([
            SystemMessage(content=system_prompt),
            *messages
        ])

        # Handle tool calls if any
        if response.tool_calls:
            tool_messages = []

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Add context for sales tickets
                if tool_name == "create_support_ticket" and "ticket_type" not in tool_args:
                    tool_args["ticket_type"] = "sales"

                # Find and execute the tool
                tool_func = None
                for tool in telecorp_tools:
                    if tool.name == tool_name:
                        tool_func = tool
                        break

                if tool_func:
                    try:
                        tool_result = await tool_func.ainvoke(tool_args)
                        tool_messages.append({
                            "role": "tool",
                            "content": str(tool_result),
                            "tool_call_id": tool_call["id"]
                        })
                    except Exception as e:
                        tool_messages.append({
                            "role": "tool",
                            "content": f"I'd be happy to help you with that! Let me connect you with our sales team for personalized assistance.",
                            "tool_call_id": tool_call["id"]
                        })

            # Get final response after tool execution
            if tool_messages:
                final_response = await sales_llm.ainvoke([
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
        print(f"Sales agent error: {e}")
        # Fallback response
        error_response = AIMessage(
            content="I apologize for the technical difficulty. Please contact our sales team at 1-800-TELECORP, and I'll make sure you get all the information you need about our great plans and pricing!"
        )

        return {
            **state,
            "messages": messages + [error_response]
        }