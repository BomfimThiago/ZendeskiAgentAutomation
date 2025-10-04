"""
Utility functions and constants for TeleCorp LangGraph tools.

This module contains helper functions, constants, and shared utilities
used across multiple tool implementations.
"""

from typing import Tuple, Optional, List


# ============================================================================
# CONSTANTS
# ============================================================================

STATUS_EMOJIS = {
    "new": "🆕",
    "open": "📂",
    "pending": "⏳",
    "hold": "⏸️",
    "solved": "✅",
    "closed": "📁",
}

PRIORITY_EMOJIS = {
    "low": "🔵",
    "normal": "🟢",
    "high": "🟡",
    "urgent": "🔴",
}

VALIDATION_MESSAGES = {
    "missing_name_email_support": """
        I'd be happy to create a support ticket for you! To ensure our team can follow up properly, I'll need to get some information from you first.

        Could you please provide:
        • Your full name
        • Your email address

        Once I have this information, I'll create your support ticket right away.
    """,
    "missing_name_email_sales": """
        I'm excited to help you with TeleCorp services! To ensure our sales team can provide you with personalized assistance and follow up properly, I'll need to get some information from you first.

        Could you please provide:
        • Your full name
        • Your email address

        Once I have this information, I'll prioritize your sales inquiry and get you connected with our best specialists!
    """,
    "missing_email_support": "Thanks, {name}! I have your name, but I'll also need your email address so our support team can follow up with you directly.\n\nCould you please provide your email address? Once I have that, I'll create your support ticket immediately.",
    "missing_email_sales": """Great to meet you, {name}! I'm excited to help you find the perfect TeleCorp solution. To ensure our sales team can follow up with personalized pricing and options, I'll need your email address and phone number.

        Could you please provide:
        • Your email address
        • Your phone number

        Once I have this information, I'll create a high-priority sales ticket and you'll hear from our specialists within hours!
    """,
    "missing_phone": "Perfect, {name}! I have your email ({email}). For the best sales experience, I'd also like to get your phone number so our sales specialists can reach you directly for faster service.\n\nCould you please provide your phone number? This ensures you get the quickest response from our team!",
}

HIDDEN_TICKET_TAGS = ["[SALES]", "[HOT LEAD]", "[LEAD]"]
HIDDEN_TAG_FIELDS = ["sales", "lead", "hot_lead"]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_customer_info(
    name: str, email: str, phone: str = None, ticket_type: str = "support"
) -> Tuple[bool, Optional[str]]:
    """
    Validate customer information and return appropriate message if missing.

    Args:
        name: Customer name
        email: Customer email
        phone: Customer phone (optional)
        ticket_type: 'support' or 'sales' for appropriate messaging

    Returns:
        Tuple of (is_valid, error_message)
    """
    invalid_names = ["TeleCorp Customer", "Prospective Customer"]

    if not name or name in invalid_names:
        msg_key = (
            "missing_name_email_sales"
            if ticket_type == "sales"
            else "missing_name_email_support"
        )
        return False, VALIDATION_MESSAGES[msg_key]

    if not email:
        msg_key = (
            "missing_email_sales" if ticket_type == "sales" else "missing_email_support"
        )
        return False, VALIDATION_MESSAGES[msg_key].format(name=name)

    if ticket_type == "sales" and not phone:
        return False, VALIDATION_MESSAGES["missing_phone"].format(
            name=name, email=email
        )

    return True, None


# ============================================================================
# FORMATTING FUNCTIONS
# ============================================================================


def format_customer_info(name: str, email: str = None, phone: str = None) -> str:
    """Format customer information for ticket description."""
    info = f"Name: {name}"
    if email:
        info += f", Email: {email}"
    if phone:
        info += f", Phone: {phone}"
    return info


def build_sales_context(interest_level: str, conversation_summary: str) -> str:
    """Build sales context for ticket description."""
    return f"""
        Interest Level: {interest_level}
        Conversation Summary: {conversation_summary}

        Sales Notes:
        - Customer engaged with AI agent about TeleCorp services
        - Qualified lead requiring sales follow-up
        - Opportunity for immediate conversion
    """


def get_status_display(status: str) -> str:
    """Get emoji + status display."""
    emoji = STATUS_EMOJIS.get(status, "📄")
    return f"{emoji} {status.title()}"


def get_priority_display(priority: str) -> str:
    """Get emoji + priority display."""
    emoji = PRIORITY_EMOJIS.get(priority, "📋")
    return f"{emoji} {priority.title()}"


# ============================================================================
# TICKET FILTERING FUNCTIONS
# ============================================================================


def is_customer_visible_ticket(ticket) -> bool:
    """Check if ticket should be visible to customers (hide internal sales/lead tickets)."""
    if any(tag in ticket.subject.upper() for tag in HIDDEN_TICKET_TAGS):
        return False

    if hasattr(ticket, "tags") and ticket.tags:
        if any(tag in HIDDEN_TAG_FIELDS for tag in ticket.tags):
            return False

    return True


def filter_customer_visible_tickets(tickets: List) -> List:
    """Filter tickets to only show customer-visible ones."""
    return [ticket for ticket in tickets if is_customer_visible_ticket(ticket)]


def format_ticket_list(tickets: List, max_display: int = 5) -> str:
    """Format a list of tickets with emojis and status."""
    ticket_lines = []

    for i, ticket in enumerate(tickets[:max_display], 1):
        emoji = STATUS_EMOJIS.get(ticket.status, "📄")
        ticket_lines.append(
            f"{i}. {emoji} Ticket #{ticket.id}: {ticket.subject} ({ticket.status.upper()})"
        )

    if len(tickets) > max_display:
        ticket_lines.append(f"... and {len(tickets) - max_display} more tickets")

    return "\n".join(ticket_lines)
