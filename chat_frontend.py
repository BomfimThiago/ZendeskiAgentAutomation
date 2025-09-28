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
sys.path.insert(0, '.')

from src.integrations.zendesk.langgraph_agent.graphs.telecorp_graph import create_telecorp_graph
from src.integrations.zendesk.langgraph_agent.state.conversation_state import ConversationState


async def run_chat():
    """Run the interactive chat interface."""

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

            # Create initial state
            initial_state = ConversationState(
                messages=[],
                user_input=user_input,
                assistant_response="",
                session_key="",
                ticket_id=None,
                user_id=None,
                security_check=None,
                is_secure=False,
                ticket_context=None,
                user_context=None,
                conversation_history=[],
                memory_loaded=False,
                route_decision="",
                requires_zendesk_update=False,
                final_response="",
                response_validated=False,
                error_occurred=False,
                error_message="",
                workflow_step="",
                processing_time=0.0,
                metadata={}
            )

            # Process through LangGraph workflow
            with SuppressOutput():
                result = await graph.ainvoke(initial_state)

            # Display AI response
            ai_response = result.get("final_response", "I apologize, I couldn't process your request.")
            print(f"\n🤖 Alex: {ai_response}")

        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("🔄 Please try again or contact support at 1-800-TELECORP")


if __name__ == "__main__":
    print("Starting TeleCorp LangGraph Chat...")
    asyncio.run(run_chat())