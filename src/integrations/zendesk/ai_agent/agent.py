"""
Main AI Agent orchestration for Zendesk customer support.

This module contains the core AI agent that handles all validation,
API calls, and business logic for TeleCorp customer support using LangChain.
"""

import logging
from typing import Optional, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from .config import ai_config
from .prompts.persona import TELECORP_PERSONA
from .memory.memory import AgentMemoryManager
from .guardrails import InputValidator, ThreatLevel, ViolationType
from src.core.logging_config import LoggerMixin, log_with_context


class TeleCorpAIAgent(LoggerMixin):
    """TeleCorp AI Agent for customer support with multi-session memory management."""

    def __init__(self):
        """Initialize the AI agent with validation."""
        self._validate_configuration()

        self.llm = ChatOpenAI(
            openai_api_key=ai_config.OPENAI_API_KEY,
            model=ai_config.DEFAULT_MODEL,
            temperature=ai_config.TEMPERATURE,
            max_tokens=ai_config.MAX_TOKENS
        )

        self.memory_manager = AgentMemoryManager(max_token_limit=ai_config.MAX_TOKENS)

        # Initialize security guardrails
        if ai_config.ENABLE_GUARDRAILS:
            self.input_validator = InputValidator()
        else:
            self.input_validator = None

        self.system_persona = SystemMessage(content=TELECORP_PERSONA)

    def _validate_configuration(self) -> None:
        """Validate all required configuration."""
        if not ai_config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")

        if not ai_config.DEFAULT_MODEL:
            raise ValueError("DEFAULT_MODEL not configured.")

    async def get_response(self, user_message: str, ticket_id: Optional[str] = None,
                          user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """
        Get AI response following natural customer service workflow.

        Args:
            user_message: The user's input message
            ticket_id: Zendesk ticket ID (use if available - has context)
            user_id: Customer user ID (for new conversations)
            session_id: Custom session ID (for testing only)

        Returns:
            AI response string

        Workflow:
            1. If ticket_id provided -> use ticket context
            2. If user_id provided -> start/continue user conversation
            3. Default to session for testing

        Raises:
            Exception: If API call fails
        """
        if not user_message or not user_message.strip():
            return "I didn't receive your message. Could you please try again?"

        try:
            # Generate session key first
            session_key = self.memory_manager.create_session_key(
                ticket_id=ticket_id,
                user_id=user_id,
                session_id=session_id or "default"
            )

            # SECURITY: Validate input with guardrails
            if self.input_validator and ai_config.ENABLE_GUARDRAILS:
                threat_level, violation_type, security_message = self.input_validator.validate_input(user_message)

                if threat_level == ThreatLevel.BLOCKED:
                    # Log security violation
                    if ai_config.LOG_SECURITY_VIOLATIONS:
                        log_with_context(
                            self.logger,
                            logging.WARNING,
                            f"Security violation detected: {violation_type.value if violation_type else 'unknown'}",
                            user_message_preview=user_message[:50] + "..." if len(user_message) > 50 else user_message,
                            threat_level=threat_level.value,
                            violation_type=violation_type.value if violation_type else None,
                            session_key=session_key,
                            ticket_id=ticket_id,
                            user_id=user_id
                        )

                    return security_message

            memory = self.memory_manager.get_memory(session_key)

            messages = memory.build_context_messages(self.system_persona, user_message.strip())

            response = await self.llm.ainvoke(messages)

            ai_response = response.content

            memory.save_interaction(user_message.strip(), ai_response)

            return ai_response

        except Exception as e:
            log_with_context(
                self.logger,
                logging.ERROR,
                "AI service error occurred during response generation",
                error=str(e),
                error_type=type(e).__name__,
                session_key=session_key,
                user_message_length=len(user_message.strip()),
                ticket_id=ticket_id,
                user_id=user_id,
                session_id=session_id
            )

            return ai_config.TECHNICAL_DIFFICULTIES_MESSAGE

    def reset_conversation(self, ticket_id: Optional[str] = None, user_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> None:
        """
        Reset conversation history for a specific session.

        Args:
            ticket_id: Zendesk ticket ID
            user_id: Customer user ID
            session_id: Custom session ID (for testing)
        """
        session_key = self.memory_manager.create_session_key(
            ticket_id=ticket_id,
            user_id=user_id,
            session_id=session_id or "default"
        )
        self.memory_manager.clear_session(session_key)

    def get_conversation_length(self, ticket_id: Optional[str] = None, user_id: Optional[str] = None,
                               session_id: Optional[str] = None) -> int:
        """
        Get number of messages in conversation for a specific session.

        Args:
            ticket_id: Zendesk ticket ID
            user_id: Customer user ID
            session_id: Custom session ID (for testing)

        Returns:
            Number of messages in the session
        """
        session_key = self.memory_manager.create_session_key(
            ticket_id=ticket_id,
            user_id=user_id,
            session_id=session_id or "default"
        )
        memory = self.memory_manager.get_memory(session_key)
        return memory.get_conversation_length()

    def get_active_sessions(self) -> List[str]:
        """Get list of all active conversation sessions."""
        return self.memory_manager.get_active_sessions()

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about all active sessions."""
        return self.memory_manager.get_session_stats()

    def get_memory_for_ticket(self, ticket_id: str):
        """
        Get memory instance for a specific Zendesk ticket.

        Args:
            ticket_id: Zendesk ticket ID

        Returns:
            AgentConversationMemory instance for the ticket
        """
        return self.memory_manager.get_memory_for_ticket(ticket_id)