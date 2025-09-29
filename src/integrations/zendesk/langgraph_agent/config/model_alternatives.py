"""
Alternative Model Configurations for Lower Token Usage

These models provide good quality while consuming fewer tokens than GPT-4.
"""

from typing import Dict, Any

# Model configurations with pros/cons
MODEL_ALTERNATIVES = {
    "gpt-3.5-turbo": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 500,
        "pros": [
            "16k context window",
            "5-10x cheaper than GPT-4",
            "Faster response times",
            "Good for routing decisions and simple conversations",
        ],
        "cons": [
            "Less capable at complex reasoning",
            "May miss nuanced customer needs",
        ],
        "use_for": ["routing", "simple_queries", "greetings"],
    },
    "gpt-3.5-turbo-1106": {
        "model": "gpt-3.5-turbo-1106",
        "temperature": 0.3,
        "max_tokens": 500,
        "pros": [
            "16k context window",
            "Better instruction following than base 3.5",
            "Good JSON mode support",
            "5-10x cheaper than GPT-4",
        ],
        "cons": ["Still less capable than GPT-4 for complex tasks"],
        "use_for": ["routing", "tool_calls", "structured_outputs"],
    },
    "gpt-4o-mini": {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 500,
        "pros": [
            "128k context window",
            "Much cheaper than GPT-4 (about 60% less)",
            "Better quality than GPT-3.5",
            "Good balance of cost and performance",
        ],
        "cons": ["Not as capable as full GPT-4 for complex reasoning"],
        "use_for": ["routing", "sales", "support", "general_conversation"],
    },
    "claude-3-haiku": {
        "provider": "anthropic",
        "model": "claude-3-haiku-20240307",
        "temperature": 0.3,
        "max_tokens": 500,
        "pros": [
            "200k context window",
            "Very fast and cheap",
            "Good for simple tasks",
            "Excellent instruction following",
        ],
        "cons": [
            "Requires Anthropic API key",
            "Less capable than Claude 3 Sonnet/Opus",
        ],
        "use_for": ["routing", "simple_support", "faq_responses"],
    },
}


def get_model_config_by_role(role: str) -> Dict[str, Any]:
    """
    Get recommended model configuration based on agent role.

    Args:
        role: Agent role (supervisor, sales, support, billing)

    Returns:
        Model configuration dictionary
    """
    role_to_model = {
        "supervisor": "gpt-3.5-turbo-1106",  # Fast routing decisions
        "sales": "gpt-4o-mini",  # Better quality for lead capture
        "support": "gpt-4o-mini",  # Good balance for technical help
        "billing": "gpt-3.5-turbo",  # Simple queries mostly
    }

    model_name = role_to_model.get(role, "gpt-3.5-turbo")
    return MODEL_ALTERNATIVES[model_name]


# Hybrid approach: Use cheaper models for simple tasks, GPT-4 for complex ones
HYBRID_CONFIG = {
    "routing_model": "gpt-3.5-turbo-1106",  # For routing decisions
    "conversation_model": "gpt-4o-mini",  # For customer conversations
    "complex_model": "gpt-4",  # For complex issues only
    "max_tokens_routing": 200,  # Minimal tokens for routing
    "max_tokens_conversation": 500,  # Moderate for conversations
    "max_tokens_complex": 1000,  # More for complex tasks
}
