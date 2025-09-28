"""
Conversation memory management for TeleCorp AI agent.

This module handles storing and retrieving conversation context
to maintain continuity across customer support interactions.
"""

from typing import List, Dict, Any, Optional
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage


class AgentConversationMemory:
    """Manages conversation memory for a single session/conversation."""

    def __init__(self, session_id: str, max_token_limit: Optional[int] = None):
        """
        Initialize conversation memory for a specific session.

        Args:
            session_id: Unique identifier for this conversation session
            max_token_limit: Optional limit for conversation tokens
        """
        self.session_id = session_id
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key=f"chat_history_{session_id}"
        )
        self.max_token_limit = max_token_limit

    def add_user_message(self, message: str) -> None:
        """Add user message to memory."""
        self.memory.chat_memory.add_user_message(message)

    def add_ai_message(self, message: str) -> None:
        """Add AI message to memory."""
        self.memory.chat_memory.add_ai_message(message)

    def get_messages(self) -> List[BaseMessage]:
        """Get all messages from memory."""
        return self.memory.chat_memory.messages

    def clear(self) -> None:
        """Clear all conversation history."""
        self.memory.clear()

    def get_conversation_length(self) -> int:
        """Get number of messages in conversation."""
        return len(self.memory.chat_memory.messages)

    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        """
        Get recent messages from conversation.

        Args:
            limit: Number of recent messages to return

        Returns:
            List of recent messages
        """
        messages = self.memory.chat_memory.messages
        return messages[-limit:] if len(messages) > limit else messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory to dictionary format."""
        return {
            "messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content
                }
                for msg in self.memory.chat_memory.messages
            ],
            "message_count": len(self.memory.chat_memory.messages)
        }

    def build_context_messages(self, system_message: SystemMessage, user_input: str) -> List[BaseMessage]:
        """
        Build complete message list for LLM including system message and history.

        Args:
            system_message: System prompt/persona
            user_input: Current user input

        Returns:
            Complete list of messages for LLM
        """
        chat_history = self.get_messages()
        return [system_message] + chat_history + [HumanMessage(content=user_input)]

    def save_interaction(self, user_input: str, ai_response: str) -> None:
        """
        Save a complete user-AI interaction to memory.

        Args:
            user_input: The user's message
            ai_response: The AI's response
        """
        self.add_user_message(user_input)
        self.add_ai_message(ai_response)


class AgentMemoryManager:
    """
    Manages multiple conversation sessions for TeleCorp AI agent.

    This class handles memory isolation between different users, tickets,
    and conversation sessions to prevent context leakage.
    """

    def __init__(self, max_token_limit: Optional[int] = None):
        """
        Initialize the memory manager.

        Args:
            max_token_limit: Optional limit for conversation tokens per session
        """
        self.sessions: Dict[str, AgentConversationMemory] = {}
        self.max_token_limit = max_token_limit

    @staticmethod
    def create_session_key(ticket_id: Optional[str] = None, user_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> str:
        """
        Create a session key following natural customer service workflow.

        Args:
            ticket_id: Zendesk ticket ID (preferred if available)
            user_id: Customer user ID (for new conversations)
            session_id: Custom session identifier (for testing)

        Returns:
            Session key for memory storage

        Workflow:
            1. If ticket exists -> use ticket context
            2. If no ticket -> start user conversation
            3. Custom session for testing only

        Examples:
            create_session_key(ticket_id="12345") -> "ticket_12345"
            create_session_key(user_id="john_doe") -> "user_john_doe"
            create_session_key(session_id="default") -> "session_default"
        """
        if ticket_id:
            return f"ticket_{ticket_id}"
        elif user_id:
            return f"user_{user_id}"
        elif session_id:
            return f"session_{session_id}"
        else:
            raise ValueError("Must provide ticket_id, user_id, or session_id")

    def get_memory(self, session_key: str) -> AgentConversationMemory:
        """
        Get or create memory for a specific session.

        Args:
            session_key: Unique session identifier

        Returns:
            AgentConversationMemory instance for the session
        """
        if session_key not in self.sessions:
            self.sessions[session_key] = AgentConversationMemory(
                session_id=session_key,
                max_token_limit=self.max_token_limit
            )
        return self.sessions[session_key]

    def get_memory_for_ticket(self, ticket_id: str) -> AgentConversationMemory:
        """
        Get memory for a specific Zendesk ticket.

        Args:
            ticket_id: Zendesk ticket ID

        Returns:
            AgentConversationMemory instance for the ticket
        """
        session_key = self.create_session_key(ticket_id=ticket_id)
        return self.get_memory(session_key)

    def get_memory_for_user(self, user_id: str) -> AgentConversationMemory:
        """
        Get memory for a specific user (across all their interactions).

        Args:
            user_id: Customer user ID

        Returns:
            AgentConversationMemory instance for the user
        """
        session_key = self.create_session_key(user_id=user_id)
        return self.get_memory(session_key)

    def clear_session(self, session_key: str) -> None:
        """
        Clear memory for a specific session.

        Args:
            session_key: Session to clear
        """
        if session_key in self.sessions:
            self.sessions[session_key].clear()

    def remove_session(self, session_key: str) -> None:
        """
        Completely remove a session from memory.

        Args:
            session_key: Session to remove
        """
        if session_key in self.sessions:
            del self.sessions[session_key]

    def get_active_sessions(self) -> List[str]:
        """
        Get list of all active session keys.

        Returns:
            List of active session identifiers
        """
        return list(self.sessions.keys())

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active sessions.

        Returns:
            Dictionary with session statistics
        """
        return {
            "total_sessions": len(self.sessions),
            "sessions": {
                session_key: {
                    "message_count": memory.get_conversation_length(),
                    "session_id": memory.session_id
                }
                for session_key, memory in self.sessions.items()
            }
        }