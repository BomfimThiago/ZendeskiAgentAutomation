"""
TeleCorp LangGraph Chat Frontend

Pure frontend interface for the TeleCorp LangGraph AI agent.
All logic, memory, and reasoning is handled by the LangGraph backend.
"""

import asyncio
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

# Import the LangGraph backend
from src.integrations.zendesk.langgraph_agent.graphs.telecorp_graph import create_telecorp_graph


async def run_chat():
    """Run the interactive chat interface - pure frontend only."""

    print("🔵 TeleCorp Customer Support Chat")
    print("Type 'quit' or 'exit' to end the conversation")
    print("=" * 50)

    # Initialize LangGraph backend
    try:
        graph = create_telecorp_graph()
    except Exception as e:
        print(f"\n❌ Error initializing LangGraph backend: {e}")
        return

    # Generate unique session ID for this conversation
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    print(f"📱 Session ID: {session_id}")
    print("=" * 50)

    print("\n🤖 Alex: Hi there! I'm Alex from TeleCorp customer support. I'm here to help you with any questions about your service or help you find the right plan for your needs. What can I assist you with today?")

    # Chat loop - just collect input and display output
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for contacting TeleCorp! Have a great day!")
                break

            if not user_input:
                continue

            # Send to LangGraph backend with session thread for memory persistence
            config = {"configurable": {"thread_id": session_id}}

            # Show typing indicator
            print("🤖 Alex is typing...")

            # Invoke the graph with user message
            result = await graph.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config
            )

            # Extract and display the AI response
            if result and "messages" in result:
                # Find the last AI message in the response
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        print(f"\n🤖 Alex: {msg.content}")
                        break

        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or contact support at 1-800-TELECORP")


if __name__ == "__main__":
    print("Starting TeleCorp LangGraph Chat...")
    asyncio.run(run_chat())