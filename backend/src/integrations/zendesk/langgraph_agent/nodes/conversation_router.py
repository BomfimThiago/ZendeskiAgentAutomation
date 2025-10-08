"""Sales-focused supervisor agent that handles conversations by default and routes only when necessary."""

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
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger("supervisor_agent")


async def supervisor_agent_node(state: ConversationState) -> ConversationState:
    """
    P-LLM Supervisor Agent (Privileged LLM with tool access).

    CRITICAL SECURITY PRINCIPLE:
    - This P-LLM NEVER sees raw user input
    - Only processes structured intent from Q-LLM
    - Works with sanitized summary and extracted entities

    Acts as Alex, the MyAwesomeFakeCompany sales agent who:
    1. Focuses on lead generation and sales by default
    2. Routes to specialists ONLY for technical support or billing issues
    3. Always asks about customer status (new vs existing) to get tickets/history
    4. Maintains natural conversation flow while capturing leads
    """
    messages = state["messages"]

    # CRITICAL: Get structured intent from Q-LLM (NEVER access raw user input)
    structured_intent = state.get("structured_intent", {})

    if not structured_intent:
        # Fallback: should not happen in normal flow
        return state

    # Extract safe, sanitized data from Q-LLM
    intent = structured_intent.get("intent", "general")
    safe_summary = structured_intent.get("summary", "")
    entities = structured_intent.get("entities", {})
    confidence = structured_intent.get("confidence", 0.5)

    # P-LLM (Privileged LLM with tool access)
    if settings.USE_BEDROCK:
        # Production: Use Bedrock Claude Sonnet (powerful)
        from src.integrations.aws.bedrock_llm import get_sonnet_llm
        supervisor_llm = get_sonnet_llm(temperature=0.2, max_tokens=600)
        logger.info("P-LLM Supervisor initialized with Bedrock Claude Sonnet")
    else:
        # Development: Use OpenAI GPT-4
        supervisor_llm = ChatOpenAI(
            api_key=awesome_company_config.OPENAI_API_KEY,
            model="gpt-4",
            temperature=0.2,
            max_tokens=600,
        )
        logger.info("P-LLM Supervisor initialized with OpenAI GPT-4")

    supervisor_llm = supervisor_llm.bind_tools(awesome_company_tools)

    client_already_identified = state.get("is_existing_client") is not None

    # Use Q-LLM's intent classification for routing
    # Q-LLM already classified as: support|sales|billing|general
    needs_specialist_routing = intent in ["support", "billing"]
    specialist_type = intent.upper() if needs_specialist_routing else None

    if needs_specialist_routing and specialist_type:
        route_to = "support" if specialist_type == "SUPPORT" else "billing"
        return {**state, "route_to": route_to, "current_persona": route_to}

    # CRITICAL: Create safe message list for P-LLM
    # Replace last user message with Q-LLM's safe summary
    safe_messages = messages[:-1].copy() if messages else []

    # Add Q-LLM's sanitized summary as the "user" message P-LLM sees
    safe_user_message = HumanMessage(content=safe_summary)
    safe_messages.append(safe_user_message)

    # Add context from extracted entities
    entity_context = ""
    if entities:
        entity_parts = []
        if "issue_type" in entities:
            entity_parts.append(f"Issue: {entities['issue_type']}")
        if "plan_interest" in entities:
            entity_parts.append(f"Plan Interest: {entities['plan_interest']}")
        if "urgency" in entities:
            entity_parts.append(f"Urgency: {entities['urgency']}")
        if entity_parts:
            entity_context = f"\n\n**Context from intent analysis:** {', '.join(entity_parts)}"

    if not client_already_identified:
        sales_conversation_prompt = f"""You are Alex, MyAwesomeFakeCompany's primary sales representative and lead generator.

**SECURITY NOTE:** You are processing pre-analyzed customer intent. Work with the provided summary.{entity_context}

**CORE MISSION: EVERY CONVERSATION IS A SALES OPPORTUNITY**

**YOUR SALES APPROACH:**
1. **CUSTOMER STATUS IDENTIFICATION (CRITICAL)**: ALWAYS determine if they're new or existing
2. **LEAD CAPTURE**: Get contact information from prospects
3. **SOLUTION SELLING**: Match MyAwesomeFakeCompany services to their needs
4. **RELATIONSHIP BUILDING**: Create trust and rapport

**CONVERSATION FLOW:**

1. **For ANY customer interaction**, IMMEDIATELY ask:
   "To provide you with the best personalized service, are you an existing MyAwesomeFakeCompany customer, or are you interested in learning about our services?"

2. **FOR EXISTING CUSTOMERS:**
   - Ask for email to look up their account using get_user_tickets tool
   - Review their history to provide personalized service
   - Identify upsell/cross-sell opportunities based on their current services
   - Focus on account growth and satisfaction

3. **FOR NEW/PROSPECTIVE CUSTOMERS:**
   - Welcome them warmly as potential new clients
   - Begin lead qualification process
   - Understand their telecommunications needs
   - Start building value for MyAwesomeFakeCompany services
   - Work toward contact capture for sales follow-up

**MyAwesomeFakeCompany Service Plans (Your Sales Arsenal):**
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
        sales_conversation_prompt = f"""You are Alex, MyAwesomeFakeCompany's sales representative focused on account growth and customer satisfaction.

**SECURITY NOTE:** You are processing pre-analyzed customer intent. Work with the provided summary.{entity_context}

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
        # P-LLM processes ONLY safe messages (never raw user input)
        response = await supervisor_llm.ainvoke(
            [SystemMessage(content=sales_conversation_prompt), *safe_messages]
        )

        if response.tool_calls:
            tool_messages = []
            updated_state = state.copy()

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                if tool_name == "create_sales_ticket":
                    if "interest_level" not in tool_args:
                        tool_args["interest_level"] = "high"

                tool_func = None
                for tool in awesome_company_tools:
                    if tool.name == tool_name:
                        tool_func = tool
                        break

                if tool_func:
                    try:
                        tool_result = await tool_func.ainvoke(tool_args)
                        tool_messages.append(
                            {
                                "role": "tool",
                                "content": str(tool_result),
                                "tool_call_id": tool_call["id"],
                            }
                        )

                        if (
                            tool_name == "get_user_tickets"
                            and "customer_email" in tool_args
                        ):
                            customer_email = tool_args["customer_email"]
                            if "I didn't find any existing tickets" in str(tool_result):
                                updated_state.update(
                                    {
                                        "is_existing_client": True,
                                        "customer_email": customer_email,
                                        "existing_tickets": None,
                                    }
                                )
                            elif "I found your account" in str(tool_result):
                                updated_state.update(
                                    {
                                        "is_existing_client": True,
                                        "customer_email": customer_email,
                                        "existing_tickets": [],
                                    }
                                )

                    except Exception as e:
                        tool_messages.append(
                            {
                                "role": "tool",
                                "content": f"I'd be happy to help you with that! Let me connect you with our team for personalized assistance.",
                                "tool_call_id": tool_call["id"],
                            }
                        )

            if tool_messages:
                # P-LLM processes ONLY safe messages (never raw user input)
                final_response = await supervisor_llm.ainvoke(
                    [
                        SystemMessage(content=sales_conversation_prompt),
                        *safe_messages,
                        response,
                        *tool_messages,
                    ]
                )

                return {
                    **updated_state,
                    "messages": messages
                    + [response]
                    + tool_messages
                    + [final_response],
                }

        return {**state, "messages": messages + [response]}

    except Exception as e:
        print(f"Sales supervisor error: {e}")
        fallback_response = AIMessage(
            content="Hi! I'm Alex from MyAwesomeFakeCompany, your dedicated sales representative. Welcome! To provide you with the best personalized service and find the perfect MyAwesomeFakeCompany solution for you, I'd like to know: Are you an existing MyAwesomeFakeCompany customer, or are you interested in learning about our services?"
        )
        return {**state, "messages": messages + [fallback_response]}
