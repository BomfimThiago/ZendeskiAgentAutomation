"""
Zendesk ticket configurations for different support types.

This module defines the ticket types, priorities, tags, and prefixes
for different categories of customer support requests.
"""

# Support ticket configurations
SUPPORT_TICKET_CONFIGS = {
    "billing": {
        "zendesk_type": "problem",
        "priority": "high",
        "tags": ["billing", "payment", "customer_service"],
        "subject_prefix": "[BILLING]",
    },
    "technical": {
        "zendesk_type": "incident",
        "priority": "normal",
        "tags": ["technical", "support", "troubleshooting"],
        "subject_prefix": "[TECH]",
    },
    "cancellation": {
        "zendesk_type": "task",
        "priority": "high",
        "tags": ["cancellation", "retention", "churn_risk"],
        "subject_prefix": "[RETENTION]",
    },
    "general": {
        "zendesk_type": "question",
        "priority": "normal",
        "tags": ["general", "inquiry", "information"],
        "subject_prefix": "[INFO]",
    },
}

# Sales ticket configuration
SALES_TICKET_CONFIG = {
    "zendesk_type": "task",
    "subject_prefix": "[HOT LEAD] [SALES]",
    "tags_base": ["sales", "new_customer", "revenue_opportunity", "hot_lead"],
}


def get_support_ticket_config(ticket_type: str) -> dict:
    """
    Get configuration for a support ticket type.

    Args:
        ticket_type: Type of support ticket (billing, technical, cancellation, general)

    Returns:
        Dictionary containing zendesk_type, priority, tags, and subject_prefix
    """
    return SUPPORT_TICKET_CONFIGS.get(
        ticket_type.lower(), SUPPORT_TICKET_CONFIGS["general"]
    )


def get_sales_ticket_tags(interest_level: str) -> list:
    """
    Get tags for a sales ticket based on interest level.

    Args:
        interest_level: Customer interest level (low, medium, high)

    Returns:
        List of tags including base sales tags and interest level tag
    """
    tags = SALES_TICKET_CONFIG["tags_base"].copy()
    tags.append(f"interest_{interest_level}")
    return tags


def get_sales_ticket_priority(interest_level: str) -> str:
    """
    Get priority for a sales ticket based on interest level.

    Args:
        interest_level: Customer interest level (low, medium, high)

    Returns:
        Priority level string (high for high interest, normal otherwise)
    """
    return "high" if interest_level == "high" else "normal"
