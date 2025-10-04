"""
Enhanced guardrail nodes using comprehensive security module.

This module provides multi-layer security validation combining:
- Pattern-based prompt injection detection
- Heuristic analysis
- Trust scoring
- Output sanitization (URL/image/DNS exfiltration prevention)
- Data provenance tracking
"""

from typing import List, Dict, Any, Tuple
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import re

from src.integrations.zendesk.langgraph_agent.state.conversation_state import (
    ConversationState,
)
from src.integrations.zendesk.langgraph_agent.config.langgraph_config import (
    telecorp_config,
)
from src.security import (
    InputValidator,
    OutputSanitizer,
    TrustLevel,
    PromptInjectionDetected,
    DataExfiltrationAttempt
)
from src.core.logging_config import get_logger

logger = get_logger("guardrail_node")


class SecurityValidator:
    """Enhanced security validator using the comprehensive security module."""

    def __init__(self):
        # Initialize security components
        self.input_validator = InputValidator()
        self.output_sanitizer = OutputSanitizer()

        # Keep LLM for semantic analysis as fallback
        self.validator_llm = ChatOpenAI(
            api_key=telecorp_config.OPENAI_API_KEY,
            model="gpt-3.5-turbo-1106",
            temperature=0.0,
            max_tokens=150,
        )

        # Critical danger patterns (still useful for immediate blocking)
        self.critical_danger_patterns = [
            r"\b(bomb|explosive|weapon|grenade)\s+(instructions?|tutorial|guide|how\s+to)",
            r"\b(hack|breach|exploit)\s+(system|network|account)",
            r"\bhow\s+to\s+(kill|murder|harm)\s+",
            r"\b(illegal\s+drugs|meth|cocaine|heroin)\s+(recipe|instructions?|how\s+to\s+make)",
        ]

        self.compiled_danger_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.critical_danger_patterns
        ]

    async def validate_input(
        self, user_message: str, conversation_context: str = "",
        user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> Tuple[bool, str, str, Dict[str, Any]]:
        """
        Enhanced validation using comprehensive security module.

        Returns:
            Tuple of (is_safe, threat_type, safe_response, security_context)
        """

        # Critical danger patterns (immediate blocking)
        for pattern in self.compiled_danger_patterns:
            if pattern.search(user_message):
                logger.warning(
                    f"Blocked critical dangerous content: {user_message[:100]}..."
                )
                return (
                    False,
                    "inappropriate",
                    "I cannot provide assistance with harmful or illegal activities. I'm here to help with TeleCorp services. What can I assist you with today?",
                    {}
                )

        # Use security module for multi-layer validation
        validation_result = self.input_validator.validate(
            text=user_message,
            user_id=user_id,
            session_id=session_id
        )

        # Extract customer name for personalized responses
        customer_name = ""
        if conversation_context:
            name_patterns = [
                r"I'm\s+([A-Za-z]+)",
                r"I am\s+([A-Za-z]+)",
                r"My name is\s+([A-Za-z]+)",
                r"Call me\s+([A-Za-z]+)",
            ]
            for pattern in name_patterns:
                match = re.search(pattern, conversation_context, re.IGNORECASE)
                if match:
                    customer_name = match.group(1)
                    break

        name_part = f"{customer_name}, " if customer_name else ""

        # If blocked by security module
        if validation_result.is_blocked:
            logger.warning(
                f"Blocked by security module: {validation_result.block_reason}"
            )

            # Determine threat type from detection details
            threat_type = "prompt_injection"
            if validation_result.detection_details.get('pattern_detection', {}).get('attack_type'):
                attack_type = validation_result.detection_details['pattern_detection']['attack_type']
                if 'jailbreak' in attack_type.lower():
                    threat_type = "prompt_injection"
                elif 'inappropriate' in attack_type.lower():
                    threat_type = "inappropriate"

            return (
                False,
                threat_type,
                f"I maintain consistent professional standards, {name_part}and I'm here to help with TeleCorp services. What can I assist you with today?",
                validation_result.security_context.to_dict() if validation_result.security_context else {}
            )

        # If requires quarantine (suspicious but not blocked)
        if validation_result.requires_quarantine:
            logger.info(
                f"Message requires quarantine: {validation_result.quarantine_reasons}"
            )
            # For now, allow but mark in context (future: route to quarantined LLM)
            return (
                True,
                "",
                "",
                validation_result.security_context.to_dict() if validation_result.security_context else {}
            )

        # Safe to proceed
        return (
            True,
            "",
            "",
            validation_result.security_context.to_dict() if validation_result.security_context else {}
        )

    def sanitize_output(self, ai_message: str) -> str:
        """
        Sanitize AI output using comprehensive security module.

        Removes:
        - Data exfiltration vectors (markdown images, suspicious URLs)
        - System prompt leakage
        - Sensitive data patterns
        """

        # Use security module's output sanitizer
        sanitized = self.output_sanitizer.sanitize(
            text=ai_message,
            remove_all_urls=False  # Only remove suspicious URLs, allow legitimate ones
        )

        # Additional TeleCorp-specific sanitization
        instruction_patterns = [
            r"system\s*prompt\s*:.*?(?:\n|$)",
            r"instructions?\s*:.*?(?:\n|$)",
            r"you\s+are\s+alex.*?specialist.*?(?:\.|!)",
            r"\*\*.*?guidelines?.*?\*\*.*?(?:\n|$)",
            r"core\s+responsibilities.*?(?:\n|$)",
        ]

        for pattern in instruction_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

        # Clean up whitespace
        sanitized = re.sub(r"\n\n+", "\n\n", sanitized)
        sanitized = re.sub(r"  +", " ", sanitized)

        return sanitized.strip()


security_validator = SecurityValidator()


async def input_validation_node(state: ConversationState) -> ConversationState:
    """
    Input validation node that checks all user messages for security threats.

    This node should be the first node in the graph after START.
    """
    messages = state["messages"]

    if not messages:
        return state

    last_message = messages[-1]

    if not isinstance(last_message, HumanMessage):
        return state

    conversation_context = ""
    for msg in messages[:-1]:
        if isinstance(msg, HumanMessage):
            conversation_context += f"User: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            conversation_context += f"AI: {msg.content}\n"

    # Extract user_id and session_id from state if available
    user_id = state.get("customer_email") or state.get("customer_name")
    session_id = None  # Could be added to state in future

    is_safe, threat_type, safe_response, security_context = await security_validator.validate_input(
        last_message.content, conversation_context, user_id=user_id, session_id=session_id
    )

    if not is_safe:
        logger.warning(f"Blocked {threat_type}: {last_message.content[:100]}...")

        # Extract trust level from security context
        trust_level = security_context.get("trust_level") if security_context else None
        trust_score = security_context.get("metadata", {}).get("trust_score") if security_context else None

        return {
            **state,
            "messages": messages + [AIMessage(content=safe_response)],
            "security_blocked": True,
            "threat_type": threat_type,
            "trust_level": trust_level,
            "trust_score": trust_score,
            "security_context": security_context,
        }

    # Safe to proceed - populate security context
    trust_level = security_context.get("trust_level") if security_context else None
    trust_score = security_context.get("metadata", {}).get("trust_score") if security_context else None

    return {
        **state,
        "security_blocked": False,
        "threat_type": None,
        "trust_level": trust_level,
        "trust_score": trust_score,
        "security_context": security_context,
    }


async def output_sanitization_node(state: ConversationState) -> ConversationState:
    """
    Output sanitization node that cleans AI responses before sending to user.

    This node should be the last node before END.
    """
    messages = state["messages"]

    if not messages:
        return state

    last_message = messages[-1]

    if not isinstance(last_message, AIMessage):
        return state

    sanitized_content = security_validator.sanitize_output(last_message.content)

    if sanitized_content != last_message.content:
        logger.info("Sanitized AI output to remove sensitive information")

        sanitized_messages = messages[:-1] + [AIMessage(content=sanitized_content)]

        return {**state, "messages": sanitized_messages}

    return state


def should_continue_after_validation(state: ConversationState) -> str:
    """
    Conditional edge function to determine if we should continue after validation.

    Returns:
        "block" if security threat detected, "continue" otherwise
    """
    if state.get("security_blocked", False):
        return "sanitize"
    return "supervisor"
