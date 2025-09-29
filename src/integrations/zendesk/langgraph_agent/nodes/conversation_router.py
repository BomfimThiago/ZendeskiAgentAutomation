"""Conversation router node using LangGraph best practices."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config


async def conversation_router_node(state: ConversationState) -> ConversationState:
    """
    Route conversation to appropriate persona based on customer intent.

    Uses LangGraph best practices:
    - Analyzes customer intent using LLM
    - Updates conversation_type and current_persona in state
    - Routes to appropriate agent node
    """
    messages = state["messages"]

    # Get the last human message to analyze intent
    last_human_message = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_message = msg
            break

    if not last_human_message:
        # Default to general support
        return {
            **state,
            "conversation_type": "general",
            "current_persona": "general_alex"
        }

    # Use LLM to classify conversation intent
    router_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-3.5-turbo",
        temperature=0.0,
        max_tokens=50
    )

    routing_prompt = """Analyze this customer message and classify the conversation type.

Customer message: "{message}"

Respond with exactly one word:
- SALES: if asking about plans, pricing, packages, signing up, upgrading, or shopping for service
- GENERAL: if asking about company info, general questions, greetings, or support

Classification:"""

    try:
        response = await router_llm.ainvoke([
            {"role": "user", "content": routing_prompt.format(message=last_human_message.content)}
        ])

        classification = response.content.strip().upper()

        if classification == "SALES":
            conversation_type = "sales"
            current_persona = "sales_alex"
        else:
            conversation_type = "general"
            current_persona = "general_alex"

        return {
            **state,
            "conversation_type": conversation_type,
            "current_persona": current_persona
        }

    except Exception as e:
        print(f"Router error: {e}")
        # Default to general on error
        return {
            **state,
            "conversation_type": "general",
            "current_persona": "general_alex"
        }