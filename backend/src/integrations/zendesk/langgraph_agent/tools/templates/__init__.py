"""
Template manager for Zendesk ticket creation.

This module provides a centralized interface for accessing all ticket templates
and configurations in a clean, organized way.
"""

from .ticket_configs import (
    get_support_ticket_config,
    get_sales_ticket_tags,
    get_sales_ticket_priority,
    SALES_TICKET_CONFIG,
)
from .ticket_descriptions import format_support_description, format_sales_description
from .customer_responses import get_customer_response, get_error_response


class TicketTemplateManager:
    """Central manager for all ticket templates and configurations."""

    @staticmethod
    def get_support_ticket_data(
        ticket_type: str, customer_info: str, request_summary: str
    ) -> dict:
        """Get complete ticket data for a support ticket."""
        config = get_support_ticket_config(ticket_type)
        description = format_support_description(
            ticket_type, customer_info, request_summary
        )
        subject = f"{config['subject_prefix']} Customer Support Request"

        return {
            "subject": subject,
            "description": description,
            "zendesk_type": config["zendesk_type"],
            "priority": config["priority"],
            "tags": config["tags"],
        }

    @staticmethod
    def get_sales_ticket_data(
        customer_info: str,
        request_summary: str,
        sales_context: str,
        interest_level: str,
    ) -> dict:
        """Get complete ticket data for a sales ticket."""
        description = format_sales_description(
            customer_info, request_summary, sales_context
        )
        subject = f"{SALES_TICKET_CONFIG['subject_prefix']} Customer Support Request"
        priority = get_sales_ticket_priority(interest_level)
        tags = get_sales_ticket_tags(interest_level)

        return {
            "subject": subject,
            "description": description,
            "zendesk_type": SALES_TICKET_CONFIG["zendesk_type"],
            "priority": priority,
            "tags": tags,
        }

    @staticmethod
    def get_customer_response(response_type: str, ticket_id: int) -> str:
        """Get customer response message."""
        return get_customer_response(response_type, ticket_id)

    @staticmethod
    def get_error_response(error_type: str = "general_error") -> str:
        """Get error response message."""
        return get_error_response(error_type)


# Create a global instance for easy import
template_manager = TicketTemplateManager()


# Export main functions for direct import
__all__ = [
    "template_manager",
    "TicketTemplateManager",
    "get_support_ticket_config",
    "get_sales_ticket_tags",
    "get_sales_ticket_priority",
    "format_support_description",
    "format_sales_description",
    "get_customer_response",
    "get_error_response",
]
