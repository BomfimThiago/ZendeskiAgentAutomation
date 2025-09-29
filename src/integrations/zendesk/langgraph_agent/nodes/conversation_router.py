"""Supervisor agent that routes customers to appropriate specialists."""

from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools


async def supervisor_agent_node(state: ConversationState) -> ConversationState:
    """
    Supervisor agent that handles conversations and routes when needed.

    Acts as Alex, the TeleCorp supervisor who:
    1. Maintains natural conversation flow
    2. Routes to specialists only when specific help is needed
    3. Remembers conversation context
    """
    messages = state["messages"]

    # Get the last human message
    last_human_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_message = msg
            break

    # Use cheaper model for routing decisions to save tokens
    supervisor_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-3.5-turbo-1106",  # Cheaper, faster, good for routing
        temperature=0.1,
        max_tokens=500  # Reduced from 1000
    ).bind_tools(telecorp_tools)

    client_already_identified = state.get("is_existing_client") is not None

    if last_human_message:
        # Check customer status for enhanced routing
        client_status = state.get("is_existing_client")
        if client_status is None:
            customer_type = "UNKNOWN (not identified yet)"
        elif client_status == False:
            customer_type = "NEW CUSTOMER"
        else:
            customer_type = "EXISTING CUSTOMER"

        routing_analysis_prompt = f"""Analyze if this customer message needs specialist routing or just friendly conversation.

Customer message: "{last_human_message.content}"
Customer type: {customer_type}

CRITICAL SALES ROUTING RULES (applies to ALL customers):
- ANY customer asking about services/plans/pricing/upgrades → ALWAYS ROUTE to sales
- NEW CUSTOMERS asking about any services → ROUTE to sales (lead capture)
- EXISTING CUSTOMERS asking about new/additional services → ROUTE to sales (upselling opportunity)
- EXISTING CUSTOMERS asking about upgrades/downgrades → ROUTE to sales
- UNKNOWN customers asking about services → ROUTE to sales (potential leads)

Does this need a specialist?
- ROUTE TO SALES if: Plans, pricing, services, packages, upgrades, new services, "what do you offer", service comparisons, "interested in", "tell me about", "looking for"
- ROUTE TO SUPPORT if: Technical issues, internet down, speed problems, router issues
- ROUTE TO BILLING if: Payment issues, account problems, cancellations, billing questions
- CONVERSATION if: ONLY pure greetings/small talk with NO service inquiry

Examples:
- "My internet is down" → ROUTE to support
- "I want to cancel my service" → ROUTE to billing
- "What plans do you offer?" → ROUTE to sales
- "I want to know your services" → ROUTE to sales
- "Tell me about residential plans" → ROUTE to sales
- "I want to upgrade my plan" → ROUTE to sales
- "What other services do you have?" → ROUTE to sales
- "I'm interested in your internet plans" → ROUTE to sales
- "Hi, I'm new to TeleCorp" (if followed by service inquiry) → ROUTE to sales
- "Hi, how are you?" → CONVERSATION (only if no service inquiry)

Respond with exactly: CONVERSATION or ROUTE"""

        try:
            analysis = await supervisor_llm.ainvoke([
                {"role": "user", "content": routing_analysis_prompt}
            ])

            needs_routing = "ROUTE" in analysis.content.upper()
        except Exception as e:
            needs_routing = False
    else:
        needs_routing = False

    if not needs_routing:
        # Check if this is initial greeting and we need to identify client status
        is_initial_greeting = (
            len(messages) <= 2 and  # First or second message
            state.get("is_existing_client") is None  # Haven't identified client yet
        )

        if not client_already_identified:
            conversation_prompt = """You are Alex, a friendly TeleCorp customer support representative. You have a natural, conversational style.

**YOUR APPROACH:**
Respond naturally to what the customer actually said. Read their message carefully and respond appropriately.

**CONVERSATION FLOW:**
1. **For greetings/introductions** (like "hi", "hello", "hey there", "I'm [name]"):
   - Respond warmly and personally
   - Welcome them naturally
   - Then ask about their customer status to provide personalized service

2. **For specific problems/requests** (like "my internet is down", "I want to cancel"):
   - Acknowledge their specific concern
   - Let them know you'll help
   - Ask about customer status to provide the right level of service

3. **For service inquiries** (like "tell me about plans", "what services"):
   - Show enthusiasm about helping with their inquiry
   - Ask about customer status to provide relevant information

**CUSTOMER STATUS QUESTION:**
Always ask: "To provide you with the best personalized service, are you an existing TeleCorp customer, or are you interested in learning about our services?"

**FOR EXISTING CUSTOMERS:**
- Ask for email to look up their account
- Use get_user_tickets tool
- Provide personalized service based on their history

**FOR NEW/INTERESTED CUSTOMERS:**
- Welcome them warmly
- Focus on helping with their specific interest

**KEY PRINCIPLE:** Match your response to what they actually said. Be natural, not robotic."""
        else:
            # Regular conversation for identified clients or ongoing chats
            conversation_prompt = """You are Alex, a friendly TeleCorp customer support supervisor.

Guidelines:
- Be warm, personable, and professional
- Remember customer details from the conversation
- Respond naturally to ongoing conversations
- Use available tools when helpful
- For general questions, provide helpful TeleCorp information
- Only mention routing to specialists for specific technical/billing/sales issues

Maintain a natural conversation while being helpful."""

        try:
            response = await supervisor_llm.ainvoke([
                SystemMessage(content=conversation_prompt),
                *messages
            ])

            # Handle tool calls if any (for client identification)
            if response.tool_calls:
                tool_messages = []
                updated_state = state.copy()

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

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
                                "content": f"I'm having trouble accessing that information right now. Let me help you with your current question instead.",
                                "tool_call_id": tool_call["id"]
                            })

                # Get final response after tool execution
                if tool_messages:
                    final_response = await supervisor_llm.ainvoke([
                        SystemMessage(content=conversation_prompt),
                        *messages,
                        response,
                        *tool_messages
                    ])

                    return {
                        **updated_state,
                        "messages": messages + [response] + tool_messages + [final_response]
                    }

            return {
                **state,
                "messages": messages + [response]
            }
        except Exception as e:
            print(f"Supervisor conversation error: {e}")
            fallback_response = AIMessage(
                content="Hi! I'm Alex from TeleCorp. Welcome! To provide you with the best personalized service, I'd like to know: Are you an existing TeleCorp customer, or are you interested in learning about our services?"
            )
            return {
                **state,
                "messages": messages + [fallback_response]
            }

    # Need to route to specialist
    routing_prompt = f"""Customer needs specialist help. Determine the best specialist:

Customer message: "{last_human_message.content}"

Specialists:
- support: Technical issues, internet problems, troubleshooting
- sales: Plans, pricing, packages, signing up, upgrades
- billing: Account issues, payments, cancellations

Respond with exactly one word: support, sales, or billing"""

    try:
        response = await supervisor_llm.ainvoke([
            {"role": "user", "content": routing_prompt}
        ])

        agent_choice = response.content.strip().lower()

        if "sales" in agent_choice:
            next_agent = "sales"
        elif "billing" in agent_choice:
            next_agent = "billing"
        else:
            next_agent = "support"


        # Route silently - no message to user about routing
        result = {
            **state,
            "route_to": next_agent,
            "current_persona": next_agent
        }
        return result

    except Exception as e:
        print(f"❌ Supervisor routing error: {e}")
        # Default to support routing silently
        result = {
            **state,
            "route_to": "support",
            "current_persona": "support"
        }
        return result