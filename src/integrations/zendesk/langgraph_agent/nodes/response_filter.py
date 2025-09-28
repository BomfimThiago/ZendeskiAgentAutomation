"""Response validation and filtering node."""

import time
from typing import Dict, Any
from langsmith import traceable

from ..state.conversation_state import ConversationState


@traceable(
    name="response_filter",
    tags=["validation", "response_filter", "telecorp"],
    metadata={"component": "output_validation", "version": "1.0"}
)
def response_filter_node(state: ConversationState) -> Dict[str, Any]:
    """
    Validate and filter AI responses for final output.

    This node performs final validation on the AI response to ensure
    it meets TeleCorp standards and doesn't contain inappropriate content.
    """
    start_time = time.time()

    assistant_response = state.get("assistant_response", "")

    # Basic response validation
    response_validated = True
    final_response = assistant_response

    # Check for empty response
    if not assistant_response or not assistant_response.strip():
        response_validated = False
        final_response = "I apologize, but I didn't generate a proper response. Could you please try again?"

    # Check for system information leakage (basic check)
    system_indicators = [
        "system prompt", "instructions", "configuration",
        "openai", "langchain", "langgraph", "api key"
    ]

    if any(indicator in assistant_response.lower() for indicator in system_indicators):
        response_validated = False
        final_response = "I'm Alex from TeleCorp customer support. Let me help you with your TeleCorp services instead."

    processing_time = time.time() - start_time

    return {
        "final_response": final_response,
        "response_validated": response_validated,
        "workflow_step": "response_validated",
        "processing_time": processing_time,
        "metadata": {
            **state.get("metadata", {}),
            "validation_time": processing_time,
            "response_length": len(final_response),
            "validation_passed": response_validated
        }
    }