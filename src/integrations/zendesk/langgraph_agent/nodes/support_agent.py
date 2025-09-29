"""Support agent for technical issues and general customer support."""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import telecorp_config
from src.integrations.zendesk.langgraph_agent.tools.telecorp_tools import telecorp_tools


async def support_agent_node(state: ConversationState) -> ConversationState:
    """
    Support agent that handles technical issues, troubleshooting, and general support.

    Uses plan-and-execute approach for complex technical problems.
    """
    messages = state["messages"]

    # Create support agent with tools
    support_llm = ChatOpenAI(
        api_key=telecorp_config.OPENAI_API_KEY,
        model="gpt-4",
        temperature=0.1,
        max_tokens=600
    ).bind_tools(telecorp_tools)

    system_prompt = """You are Alex from TeleCorp customer support. You continue the conversation seamlessly - the user doesn't know they've been routed to a specialist.

**Your Mission:**
1. **Clarify the technical issue** - Ask specific questions to understand the problem
2. **Use knowledge tools** to provide comprehensive solutions
3. **Guide the customer step-by-step** through troubleshooting
4. **Only escalate to ticket** when all knowledge-based solutions are exhausted

**Available Knowledge Tools:**
- get_telecorp_faq: General TeleCorp information and policies
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

        # Get response from support agent
        response = await support_llm.ainvoke([
            SystemMessage(content=system_prompt),
            *messages
        ])

        # Handle tool calls if any
        if response.tool_calls:
            tool_messages = []

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
                    except Exception as e:
                        tool_messages.append({
                            "role": "tool",
                            "content": f"I encountered an issue with that request. Let me try a different approach or create a support ticket for you.",
                            "tool_call_id": tool_call["id"]
                        })

            # Get final response after tool execution
            if tool_messages:
                final_response = await support_llm.ainvoke([
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
        print(f"Support agent error: {e}")
        # Fallback response
        error_response = AIMessage(
            content="I apologize for the technical difficulty. Please contact our support team at 1-800-TELECORP, and I'll make sure you get the help you need."
        )

        return {
            **state,
            "messages": messages + [error_response]
        }