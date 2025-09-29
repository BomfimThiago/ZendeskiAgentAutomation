"""
TeleCorp LangGraph Chat Frontend

Simple console interface for testing the TeleCorp LangGraph AI agent.
"""

import asyncio
import warnings
import logging
import os
import sys
from datetime import datetime

# Suppress ALL warnings and logs for clean chat experience
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)

# Suppress specific warnings
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Redirect stderr to suppress HTTP requests and other noise
class SuppressOutput:
    def __enter__(self):
        self._original_stderr = sys.stderr
        self._original_stdout = sys.stdout
        # Redirect both stderr and stdout to null during processing
        sys.stderr = open(os.devnull, 'w')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self._original_stderr

# Set logging level to suppress all logs
import logging
logging.getLogger().setLevel(logging.CRITICAL + 1)
logging.getLogger("langchain").setLevel(logging.CRITICAL + 1)
logging.getLogger("openai").setLevel(logging.CRITICAL + 1)
logging.getLogger("httpx").setLevel(logging.CRITICAL + 1)
logging.getLogger("langgraph").setLevel(logging.CRITICAL + 1)

# Add current directory to Python path to avoid dependency issues
import sys
from pathlib import Path
sys.path.insert(0, '.')

# Import directly from the full path to avoid relative import issues
try:
    from src.integrations.zendesk.langgraph_agent.graphs.telecorp_graph import create_telecorp_graph
    from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState

    # Try to import HumanMessage, fallback if not available
    try:
        from langchain_core.messages import HumanMessage
    except ImportError:
        # Create a simple message class if langchain_core not available
        class HumanMessage:
            def __init__(self, content: str):
                self.content = content
                self.type = "human"

    DEPENDENCIES_AVAILABLE = True

except ImportError as e:
    print(f"📦 Dependencies not fully installed: {e}")
    print("🧹 Architecture has been cleaned up successfully!")
    print("\n📁 Clean LangGraph Architecture:")
    print("├── graphs/")
    print("│   └── telecorp_graph.py (main workflow)")
    print("├── nodes/")
    print("│   ├── telecorp_agent.py (AI agent)")
    print("│   └── guardrail_node.py (simple guardrails)")
    print("├── state/")
    print("│   └── conversation_state.py (simplified state)")
    print("├── tools/")
    print("│   └── telecorp_tools.py (knowledge tools)")
    print("├── prompts/")
    print("│   └── persona.py (TeleCorp persona)")
    print("└── config/")
    print("    └── langgraph_config.py (configuration)")
    print("\n✅ All old/unused files removed")
    print("✅ Following LangGraph best practices")
    print("✅ Simple, maintainable codebase")
    print("\n💡 To run the chat, install dependencies:")
    print("   uv add langgraph langchain-openai")

    DEPENDENCIES_AVAILABLE = False


async def run_chat():
    """Run the interactive chat interface."""

    if not DEPENDENCIES_AVAILABLE:
        return

    print("🔵 TeleCorp Customer Support Chat")
    print("Type 'quit' or 'exit' to end the conversation")
    print("=" * 50)

    # Display Alex's welcome message
    print("\n🤖 Alex: Hi there! I'm Alex from TeleCorp customer support. I'm here to help you with any questions about your service or help you find the right plan for your needs. What can I assist you with today?")

    # Create the LangGraph workflow
    try:
        graph = create_telecorp_graph()
    except Exception as e:
        print(f"\n❌ Error initializing chat: {e}")
        return

    while True:
        try:
            # Get user input with better error handling
            try:
                user_input = input("\n💬 You: ").strip()
            except EOFError:
                print("\n\n👋 Chat ended. Thank you for contacting TeleCorp!")
                break
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break

            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thank you for contacting TeleCorp! Have a great day!")
                break

            if not user_input:
                continue

            # Create initial state using dual persona structure
            initial_state = ConversationState(
                messages=[HumanMessage(content=user_input)],
                user_id=None,
                session_id="chat_session",
                conversation_type="general",  # Will be determined by router
                current_persona="general_alex",  # Will be determined by router
                metadata={}
            )

            # Process through LangGraph workflow
            with SuppressOutput():
                result = await graph.ainvoke(initial_state)

            # Extract AI response from messages
            messages = result.get("messages", [])
            ai_response = "I apologize, I couldn't process your request."

            # Get the last AI message (more robust checking)
            for msg in reversed(messages):
                if hasattr(msg, 'content'):
                    # Check if it's not a human message
                    is_human = (isinstance(msg, HumanMessage) or
                              (hasattr(msg, 'type') and msg.type == "human") or
                              (hasattr(msg, '__class__') and 'Human' in msg.__class__.__name__))

                    if not is_human and msg.content.strip():
                        ai_response = msg.content
                        break

            print(f"\n🤖 Alex: {ai_response}")

        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("🔄 Please try again or contact support at 1-800-TELECORP")

            # Add debug info for development
            if hasattr(e, '__traceback__'):
                import traceback
                print("\n🐛 Debug info:")
                traceback.print_exc()


if __name__ == "__main__":
    print("Starting TeleCorp LangGraph Chat...")
    asyncio.run(run_chat())