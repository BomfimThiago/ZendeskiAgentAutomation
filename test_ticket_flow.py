"""
Test script for TeleCorp LangGraph Agent ticket creation flow.
Tests the conversation state persistence and ticket creation.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, '.')

from src.integrations.zendesk.langgraph_agent.graphs.telecorp_graph import create_telecorp_graph
from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState
from langchain_core.messages import HumanMessage


async def test_ticket_creation_flow():
    """Test the complete ticket creation flow."""

    print("🔵 Testing TeleCorp Ticket Creation Flow")
    print("=" * 50)

    # Create the LangGraph workflow
    try:
        graph = create_telecorp_graph()
        print("✅ Graph created successfully")
    except Exception as e:
        print(f"❌ Error creating graph: {e}")
        return False

    # Initialize conversation state
    conversation_state = None

    # Test messages simulating the problematic scenario
    test_messages = [
        "My internet connection is not working",
        "I tried restarting my router and it's still not working",
        "Thiago, bomfimdev@gmail.com"
    ]

    for i, user_input in enumerate(test_messages):
        print(f"\n--- Message {i+1} ---")
        print(f"User: {user_input}")

        try:
            # Use proper LangGraph thread-based persistence
            input_data = {
                "messages": [HumanMessage(content=user_input)]
            }

            config = {
                "configurable": {
                    "thread_id": "test_session"  # Consistent thread for test
                }
            }

            # Process through LangGraph with automatic state persistence
            result = await graph.ainvoke(input_data, config)

            print(f"✅ Message {i+1} processed successfully")

            # Extract AI response
            messages = result.get("messages", [])
            ai_response = "No response"

            for msg in reversed(messages):
                if hasattr(msg, 'content'):
                    is_human = (isinstance(msg, HumanMessage) or
                              (hasattr(msg, 'type') and msg.type == "human") or
                              (hasattr(msg, '__class__') and 'Human' in msg.__class__.__name__))

                    if not is_human and msg.content.strip():
                        ai_response = msg.content
                        break

            print(f"Alex: {ai_response[:200]}...")

            # Check for ticket creation in response or tool calls
            if ("ticket" in ai_response.lower() and "#" in ai_response) or \
               ("created" in ai_response.lower() and "ticket" in ai_response.lower()):
                print("🎫 ✅ TICKET CREATED SUCCESSFULLY!")
                return True

            # Also check if create_support_ticket was called in tool_calls
            if result["messages"] and hasattr(result["messages"][-1], 'tool_calls'):
                for tool_call in result["messages"][-1].tool_calls:
                    if tool_call.get('name') == 'create_support_ticket':
                        print("🎫 ✅ TICKET CREATION TOOL WAS CALLED!")
                        return True

        except Exception as e:
            print(f"❌ Error processing message {i+1}: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n--- Test Complete ---")
    print("❌ Expected ticket creation but none found")
    return False


if __name__ == "__main__":
    success = asyncio.run(test_ticket_creation_flow())
    if success:
        print("\n🎉 TEST PASSED: Ticket creation flow works correctly!")
        sys.exit(0)
    else:
        print("\n💥 TEST FAILED: Ticket creation flow needs investigation")
        sys.exit(1)