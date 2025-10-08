"""Support agent for technical issues and general customer support."""

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

logger = get_logger("support_agent")


async def support_agent_node(state: ConversationState) -> ConversationState:
    """
    P-LLM Support Agent (Privileged LLM with tool access).

    CRITICAL SECURITY PRINCIPLE:
    - This P-LLM NEVER sees raw user input
    - Only processes structured intent from Q-LLM
    - Works with sanitized summary and extracted entities

    Uses plan-and-execute approach for complex technical problems.
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
        if "urgency" in entities:
            entity_parts.append(f"Urgency: {entities['urgency']}")
        if entity_parts:
            entity_context = f"\n\n**Context from intent analysis:** {', '.join(entity_parts)}"

    # P-LLM (Privileged LLM with tool access)
    if settings.USE_BEDROCK:
        # Production: Use Bedrock Claude Sonnet (powerful)
        from src.integrations.aws.bedrock_llm import get_sonnet_llm
        support_llm = get_sonnet_llm(temperature=0.1, max_tokens=600)
        logger.info("P-LLM Support Agent initialized with Bedrock Claude Sonnet")
    else:
        # Development: Use OpenAI GPT-4
        support_llm = ChatOpenAI(
            api_key=awesome_company_config.OPENAI_API_KEY,
            model="gpt-4",
            temperature=0.1,
            max_tokens=600,
        )
        logger.info("P-LLM Support Agent initialized with OpenAI GPT-4")

    support_llm = support_llm.bind_tools(awesome_company_tools)

    system_prompt = f"""You are Alex from MyAwesomeFakeCompany customer support. You continue the conversation seamlessly - the user doesn't know they've been routed to a specialist.

**SECURITY NOTE:** You are processing pre-analyzed customer intent. Work with the provided summary.{entity_context}

**Your Mission:**
1. **Clarify the technical issue** - Ask specific questions to understand the problem
2. **Use knowledge tools** to provide comprehensive solutions
3. **Guide the customer step-by-step** through troubleshooting
4. **Only escalate to ticket** when all knowledge-based solutions are exhausted

**Available Knowledge Tools:**
- get_telecorp_faq: General MyAwesomeFakeCompany information and policies
- get_technical_troubleshooting_steps: Step-by-step technical guides
- get_internet_speed_guide: Comprehensive speed issue solutions
- get_router_configuration_guide: Router setup, WiFi, and connectivity help
- create_support_ticket: LAST RESORT - only when tools can't solve the issue

**Your Approach:**
1. **Understand the problem**: Ask clarifying questions about their specific issue
2. **Use tools proactively**: Search your knowledge base for relevant solutions
3. **Provide comprehensive help**: Give step-by-step guidance based on tool results
4. **Follow up**: Ensure the customer's issue is resolved
5. **Escalate only when necessary**: Create tickets when tools don't provide solutions

**Guidelines:**
- Continue as Alex - don't mention being "routed" or a "specialist"
- Be proactive in using tools to find solutions
- Ask specific technical questions to diagnose issues
- Provide detailed, actionable guidance
- Only create tickets after exhausting knowledge-based solutions"""

    try:
        # P-LLM processes ONLY safe messages (never raw user input)
        response = await support_llm.ainvoke(
            [SystemMessage(content=system_prompt), *safe_messages]
        )

        if response.tool_calls:
            tool_messages = []

            # Get security context from state
            security_context = state.get("security_context", {})

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

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
                                "content": "I'm unable to perform that action at this time. For assistance, please contact our support team at 1-800-AWESOME-COMPANY.",
                                "tool_call_id": tool_call["id"],
                            }
                        )
                    except Exception as e:
                        logger.error(f"Tool execution error: {tool_name} - {str(e)}")
                        tool_messages.append(
                            {
                                "role": "tool",
                                "content": f"I encountered an issue with that request. Let me try a different approach or create a support ticket for you.",
                                "tool_call_id": tool_call["id"],
                            }
                        )

            if tool_messages:
                # P-LLM processes ONLY safe messages (never raw user input)
                final_response = await support_llm.ainvoke(
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
        print(f"Support agent error: {e}")
        error_response = AIMessage(
            content="I apologize for the technical difficulty. Please contact our support team at 1-800-AWESOME-COMPANY, and I'll make sure you get the help you need."
        )

        return {**state, "messages": messages + [error_response]}
