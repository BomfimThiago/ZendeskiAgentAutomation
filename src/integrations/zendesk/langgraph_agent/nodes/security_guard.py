"""Security guard node for input validation and threat detection."""

import time
from typing import Dict, Any
from langsmith import traceable

from ..state.conversation_state import ConversationState
from ..state.schemas import SecurityThreat, ThreatLevel, ViolationType
from ..guardrails.llm_validator import LLMGuardrailValidator


@traceable(
    name="security_guard",
    tags=["security", "guardrails", "telecorp"],
    metadata={"component": "security_validation", "version": "2.0", "type": "llm_based"}
)
async def security_guard_node(state: ConversationState) -> Dict[str, Any]:
    """
    Validate user input against security policies and threats.

    This node acts as the first line of defense, using the existing
    InputValidator to check for jailbreak attempts, prompt injection,
    inappropriate content, and scope violations.
    """
    start_time = time.time()

    user_input = state.get("user_input", "")

    # Initialize the LLM-based validator
    validator = LLMGuardrailValidator()

    # Perform security validation using LLM
    threat_level, violation_type, security_message = await validator.validate_input(user_input)

    # Create security assessment
    security_check = SecurityThreat(
        threat_level=threat_level,
        violation_type=violation_type,
        security_message=security_message,
        blocked=(threat_level == ThreatLevel.BLOCKED)
    )

    # Determine if input is secure
    is_secure = threat_level != ThreatLevel.BLOCKED

    # If blocked, set final response immediately
    final_response = ""
    if security_check.blocked:
        final_response = security_message

    processing_time = time.time() - start_time

    # Add LangSmith metrics
    from langsmith import Client

    # Log custom metrics for LangSmith
    langsmith_metrics = {
        "security_check_duration": processing_time,
        "threat_level": threat_level.value,
        "violation_type": violation_type.value if violation_type else None,
        "input_length": len(user_input),
        "blocked": security_check.blocked,
        "telecorp_component": "security_guard"
    }

    return {
        "security_check": security_check,
        "is_secure": is_secure,
        "final_response": final_response if security_check.blocked else state.get("final_response", ""),
        "workflow_step": "security_validated",
        "processing_time": processing_time,
        "metadata": {
            **state.get("metadata", {}),
            "security_validation_time": processing_time,
            "threat_detected": security_check.blocked,
            "langsmith_metrics": langsmith_metrics
        }
    }