#!/usr/bin/env python3
"""
Test script to verify TeleCorp conversation flow works correctly.
"""

import asyncio
import uuid
from langchain_core.messages import HumanMessage, AIMessage

# Import the LangGraph backend
from src.integrations.zendesk.langgraph_agent.graphs.telecorp_graph import create_telecorp_graph


async def test_conversation():
    """Test conversation flow and memory."""

    print("🧪 Testing TeleCorp Conversation Flow")
    print("=" * 50)

    # Initialize LangGraph backend
    try:
        graph = create_telecorp_graph()
        print("✅ LangGraph backend initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing LangGraph backend: {e}")
        return

    # Generate unique session ID
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}
    print(f"📱 Session ID: {session_id}")
    print()

    # Test conversation scenarios
    test_messages = [
        "I'm Thiago, how are you?",
        "What is my name?",
        "I have a problem with my internet - it's very slow",
        "What are your pricing plans?"
    ]

    for i, user_message in enumerate(test_messages, 1):
        print(f"💬 Test {i}: {user_message}")

        try:
            # Send message to LangGraph
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=user_message)]},
                config
            )

            # Extract AI response
            if result and "messages" in result:
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        print(f"🤖 Alex: {msg.content}")
                        break

                # Debug: Show routing info
                route_to = result.get("route_to")
                if route_to:
                    print(f"🔧 Debug: Routed to {route_to}")

            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print()

    print("🎯 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_conversation())