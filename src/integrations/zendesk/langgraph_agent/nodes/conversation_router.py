"""Sales-focused supervisor agent that handles conversations by default and routes only when necessary."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools


async def supervisor_agent_node(state: ConversationState) -> ConversationState:
    """
    Sales-focused supervisor agent that handles conversations by default.

    Acts as Alex, the TeleCorp sales agent who:
    1. Focuses on lead generation and sales by default
    2. Routes to specialists ONLY for technical support or billing issues
    3. Always asks about customer status (new vs existing) to get tickets/history
    4. Maintains natural conversation flow while capturing leads
    """
    messages = state["messages"]

    # Get the last human message
    last_human_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_message = msg
            break

    # Use GPT-4 for better sales conversations
    supervisor_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-4",  # Better for sales conversations and lead capture
        temperature=0.2,
        max_tokens=600
    ).bind_tools(telecorp_tools)

    client_already_identified = state.get("is_existing_client") is not None

    # Check if we need to route AWAY from sales (only for technical support or billing)
    needs_specialist_routing = False

    if last_human_message:
        # Only check for routing AWAY from sales for specific technical or billing issues
        specialist_routing_prompt = f"""Analyze if this customer needs TECHNICAL SUPPORT or BILLING specialist (NOT sales).

Customer message: "{last_human_message.content}"

ROUTE TO SPECIALIST ONLY FOR:

🔧 TECHNICAL SUPPORT - ONLY genuine technical problems:
- Internet/WiFi not working, slow speeds, connectivity issues
- Router problems, hardware troubleshooting, configuration help
- Service outages, technical failures
- Existing service having problems

💳 BILLING SPECIALIST - ONLY account/payment issues:
- Payment problems, billing disputes, refunds
- Account cancellations, service changes
- Billing questions about existing accounts

DO NOT ROUTE for:
- General questions about plans, pricing, services (KEEP IN SALES)
- New customer inquiries (KEEP IN SALES)
- Service shopping or exploration (KEEP IN SALES)
- Greetings, introductions, general conversation (KEEP IN SALES)
- "What do you offer?" type questions (KEEP IN SALES)

Respond with ONLY: SUPPORT, BILLING, or SALES"""

        try:
            analysis = await supervisor_llm.ainvoke([
                {"role": "user", "content": specialist_routing_prompt}
            ])

            intent = analysis.content.strip().upper()
            # Only route away if it's clearly SUPPORT or BILLING
            needs_specialist_routing = intent in ["SUPPORT", "BILLING"]
            specialist_type = intent if needs_specialist_routing else None
        except Exception as e:
            needs_specialist_routing = False
            specialist_type = None
    else:
        needs_specialist_routing = False
        specialist_type = None

    # If we need specialist routing, route away
    if needs_specialist_routing and specialist_type:
        route_to = "support" if specialist_type == "SUPPORT" else "billing"
        return {
            **state,
            "route_to": route_to,
            "current_persona": route_to
        }

    # DEFAULT: Handle as sales-focused conversation with lead generation focus
    if not client_already_identified:
        # Sales-focused prompt for unidentified customers
        sales_conversation_prompt = """You are Alex, TeleCorp's primary sales representative and lead generator.

**CORE MISSION: EVERY CONVERSATION IS A SALES OPPORTUNITY**

**YOUR SALES APPROACH:**
1. **CUSTOMER STATUS IDENTIFICATION (CRITICAL)**: ALWAYS determine if they're new or existing
2. **LEAD CAPTURE**: Get contact information from prospects
3. **SOLUTION SELLING**: Match TeleCorp services to their needs
4. **RELATIONSHIP BUILDING**: Create trust and rapport

**CONVERSATION FLOW:**

1. **For ANY customer interaction**, IMMEDIATELY ask:
   "To provide you with the best personalized service, are you an existing TeleCorp customer, or are you interested in learning about our services?"

2. **FOR EXISTING CUSTOMERS:**
   - Ask for email to look up their account using get_user_tickets tool
   - Review their history to provide personalized service
   - Identify upsell/cross-sell opportunities based on their current services
   - Focus on account growth and satisfaction

3. **FOR NEW/PROSPECTIVE CUSTOMERS:**
   - Welcome them warmly as potential new clients
   - Begin lead qualification process
   - Understand their telecommunications needs
   - Start building value for TeleCorp services
   - Work toward contact capture for sales follow-up

**TeleCorp Service Plans (Your Sales Arsenal):**
- **Residential High-Speed Internet**: Starting at $39.99/month
- **Business Internet Packages**: From $79.99/month
- **Premium Unlimited Packages**: Starting at $69.99/month

**Current Promotions (CREATE URGENCY):**
- New customers get first month free
- Free installation for annual contracts
- Bundle discounts for multiple services

**SALES MINDSET:**
- Every customer is a potential lead
- Focus on their needs and pain points
- Build value before discussing price
- Create urgency with promotions
- Always work toward getting contact information

**KEY PRINCIPLE:** You're not just customer support - you're a sales professional. Every interaction should move toward lead generation or account growth."""
    else:
        # Sales-focused prompt for identified customers
        sales_conversation_prompt = """You are Alex, TeleCorp's sales representative focused on account growth and customer satisfaction.

**CUSTOMER IDENTIFIED - FOCUS ON ACCOUNT OPTIMIZATION:**

Guidelines:
- Leverage customer history from previous interactions
- Look for upsell/cross-sell opportunities
- Provide personalized service recommendations
- Use available tools to access account information
- Focus on customer lifetime value growth
- Maintain relationship while identifying expansion opportunities

**Available Tools:**
- get_user_tickets: Access customer history and identify service gaps
- get_telecorp_faq: Provide detailed service information
- create_sales_ticket: Log new opportunities for follow-up

Your goal: Maximize customer satisfaction while identifying growth opportunities."""

    try:
        response = await supervisor_llm.ainvoke([
            SystemMessage(content=sales_conversation_prompt),
            *messages
        ])

        # Handle tool calls if any (for client identification and sales activities)
        if response.tool_calls:
            tool_messages = []
            updated_state = state.copy()

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Add sales context for ticket creation
                if tool_name == "create_sales_ticket":
                    # Ensure interest level is set for sales tickets
                    if "interest_level" not in tool_args:
                        tool_args["interest_level"] = "high"  # Default to high for proactive sales

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

                        # Update state based on tool results
                        if tool_name == "get_user_tickets" and "customer_email" in tool_args:
                            customer_email = tool_args["customer_email"]
                            if "I didn't find any existing tickets" in str(tool_result):
                                updated_state.update({
                                    "is_existing_client": True,
                                    "customer_email": customer_email,
                                    "existing_tickets": None
                                })
                            elif "I found your account" in str(tool_result):
                                updated_state.update({
                                    "is_existing_client": True,
                                    "customer_email": customer_email,
                                    "existing_tickets": []
                                })

                    except Exception as e:
                        tool_messages.append({
                            "role": "tool",
                            "content": f"I'd be happy to help you with that! Let me connect you with our team for personalized assistance.",
                            "tool_call_id": tool_call["id"]
                        })

            # Get final response after tool execution
            if tool_messages:
                final_response = await supervisor_llm.ainvoke([
                    SystemMessage(content=sales_conversation_prompt),
                    *messages,
                    response,
                    *tool_messages
                ])

                return {
                    **updated_state,
                    "messages": messages + [response] + tool_messages + [final_response]
                }

        # No tools used - direct sales response
        return {
            **state,
            "messages": messages + [response]
        }

    except Exception as e:
        print(f"Sales supervisor error: {e}")
        # Fallback response with sales focus
        fallback_response = AIMessage(
            content="Hi! I'm Alex from TeleCorp, your dedicated sales representative. Welcome! To provide you with the best personalized service and find the perfect TeleCorp solution for you, I'd like to know: Are you an existing TeleCorp customer, or are you interested in learning about our services?"
        )
        return {
            **state,
            "messages": messages + [fallback_response]
        }