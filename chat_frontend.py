#!/usr/bin/env python3
"""
TeleCorp AI Agent - Console Chat Interface

Simple console frontend to chat with the TeleCorp AI agent.
All business logic and validation is handled by the AI agent module.
"""

import os
import sys
import asyncio

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.integrations.zendesk.ai_agent.agent import TeleCorpAIAgent
except ImportError as e:
    print(f"❌ Error importing AI agent: {e}")
    print("Make sure you have installed the required dependencies.")
    sys.exit(1)


class TeleCorpChatFrontend:
    """Simple console-based chat interface."""

    def __init__(self):
        """Initialize the chat frontend."""
        try:
            self.ai_agent = TeleCorpAIAgent()
        except Exception as e:
            print(f"❌ Error initializing AI agent: {e}")
            sys.exit(1)

    def display_welcome(self):
        """Display welcome message."""
        print("=" * 60)
        print("🌐 TELECORP CUSTOMER SUPPORT CHAT")
        print("=" * 60)
        print("Connected to AI Agent: Alex")
        print("Type 'quit' to end the chat")
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
                break

            if not user_input:
                continue

            # Check for quit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n🤖 Alex: Thank you for choosing TeleCorp! Have a great day!")
                break

            # Show typing indicator
            print("\n🤔 Alex is typing...")

            # Get AI response
            ai_response = await self.ai_agent.get_response(user_input)
            print(f"\n🤖 Alex: {ai_response}")


async def main():
    """Main function to run the chat interface."""
    print("🚀 Starting TeleCorp AI Chat Interface...")

    chat = TeleCorpChatFrontend()
    await chat.run_chat()

    print("\n👋 Chat session ended. Thanks for using TeleCorp AI!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Chat interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting chat: {e}")
        sys.exit(1)