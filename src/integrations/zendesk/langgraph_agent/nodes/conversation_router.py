"""Supervisor agent that routes customers to appropriate specialists."""

from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config


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

    # Create supervisor LLM for conversation
    supervisor_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-4",
        temperature=0.1,
        max_tokens=400
    )

    # Check if this needs routing to a specialist or just conversation
    if last_human_message:
        routing_analysis_prompt = f"""Analyze if this customer message needs specialist routing or just friendly conversation.

Customer message: "{last_human_message.content}"

Does this need a specialist?
- ROUTE if: Technical issues, specific billing problems, detailed plan/pricing questions, service cancellations
- CONVERSATION if: Greetings, introductions, small talk, general questions about name/identity

Examples:
- "Hi, I'm John how are you?" → CONVERSATION
- "What is my name?" → CONVERSATION
- "My internet is down" → ROUTE to support
- "I want to cancel my service" → ROUTE to billing
- "What plans do you offer?" → ROUTE to sales

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
        # Handle as natural conversation
        conversation_prompt = """You are Alex, a friendly TeleCorp customer support supervisor.

Guidelines:
- Be warm, personable, and professional
- Remember customer details from the conversation
- Respond naturally to greetings, introductions, and small talk
- If customers introduce themselves, remember their name
- For general questions, provide helpful TeleCorp information
- Only mention routing to specialists for specific technical/billing/sales issues

Maintain a natural conversation while being helpful."""

        try:
            response = await supervisor_llm.ainvoke([
                SystemMessage(content=conversation_prompt),
                *messages
            ])

            return {
                **state,
                "messages": messages + [response]
            }
        except Exception as e:
            print(f"Supervisor conversation error: {e}")
            fallback_response = AIMessage(
                content="Hi! I'm Alex from TeleCorp. How can I help you today?"
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