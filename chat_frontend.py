#!/usr/bin/env python3
"""
TeleCorp AI Agent - Console Chat Interface

Simple console frontend to chat with the TeleCorp AI agent.
All business logic and validation is handled by the AI agent module.
"""

import os
import sys
import asyncio
from pathlib import Path
import logging
import warnings
from contextlib import redirect_stderr
from io import StringIO


# AGGRESSIVELY suppress all warnings and logs
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")
logging.disable(logging.CRITICAL)

# Set PYTHONWARNINGS environment variable to ignore all warnings
os.environ["PYTHONWARNINGS"] = "ignore"

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.integrations.zendesk.ai_agent.agent import TeleCorpAIAgent
except ImportError as e:
    print(f"❌ Error importing AI agent: {e}")
    print("Make sure you have installed the required dependencies:")
    print("  pip install -r requirements/base.txt")
    sys.exit(1)


class TeleCorpChatFrontend:
    """Simple console-based chat interface."""

    def __init__(self):
        """Initialize the chat frontend."""
        self._check_environment()
        try:
            # Suppress all output during agent initialization
            with redirect_stderr(StringIO()):
                self.ai_agent = TeleCorpAIAgent()
            print("✅ AI Agent initialized successfully")
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            print("\n💡 Quick Fix:")
            print("1. Copy .env.example to .env")
            print("2. Add your OpenAI API key to .env file")
            print("3. Run: cp .env.example .env")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error initializing AI agent: {e}")
            print("\n🔍 Troubleshooting:")
            print("- Check your .env file has OPENAI_API_KEY")
            print("- Verify all dependencies are installed")
            print("- Run: pip install -r requirements/base.txt")
            sys.exit(1)

    def _check_environment(self):
        """Check if environment is properly configured."""
        env_file = Path(".env")
        if not env_file.exists():
            print("⚠️ Warning: .env file not found")
            print("💡 Create one from .env.example for proper configuration")
            print()

        # Check if OpenAI API key is set (without revealing it)
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key:
            print("⚠️ Warning: OPENAI_API_KEY not found in environment")
            print("💡 Add it to your .env file to use the AI agent")
            print()

    def display_welcome(self):
        """Display welcome message."""
        print("=" * 60)
        print("🌐 TELECORP CUSTOMER SUPPORT CHAT")
        print("=" * 60)
        print("Connected to AI Agent: Alex")
        print("Commands:")
        print("  • 'quit' or 'exit' - End the chat")
        print("  • 'reset' or 'clear' - Start fresh conversation")
        print("=" * 60)

    async def run_chat(self):
        """Main chat loop."""
        self.display_welcome()

        # Initial greeting
        print("\n🤖 Alex: Hi there! I'm Alex from TeleCorp customer support. I'm here to help you with any questions about your service or help you find the right plan for your needs. What can I assist you with today?")

        while True:
            # Get user input
            try:
                user_input = input("\n👤 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Chat interrupted. Goodbye!")
                break

            if not user_input:
                continue

            # Check for quit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n🤖 Alex: Thank you for choosing TeleCorp! Have a great day!")
                break

            # Check for reset command
            if user_input.lower() in ['reset', 'restart', 'clear']:
                self.ai_agent.reset_conversation()
                print("\n🔄 Conversation reset. How can I help you today?")
                continue

            # Show typing indicator
            print("\n🤔 Alex is typing...")

            # Get AI response with error handling (suppress all warnings/logs)
            try:
                with redirect_stderr(StringIO()):
                    ai_response = await self.ai_agent.get_response(user_input)
                print(f"\n🤖 Alex: {ai_response}")
            except Exception as e:
                print(f"\n❌ Error getting response: {e}")
                print("🔄 Please try again or type 'quit' to exit.")


async def main():
    """Main function to run the chat interface."""
    print("🚀 Starting TeleCorp AI Chat Interface...")
    print("📋 Checking system requirements...")

    try:
        chat = TeleCorpChatFrontend()
        await chat.run_chat()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return

    print("\n👋 Chat session ended. Thanks for using TeleCorp AI!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting chat: {e}")
        sys.exit(1)