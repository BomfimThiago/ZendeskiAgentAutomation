"""
Clean and simple Zendesk ticket creation tools for TeleCorp LangGraph agents.

This module provides easy-to-understand tools for creating Zendesk tickets
using the existing Zendesk service layer and organized templates.
"""

from typing import Optional, Tuple, List
from langchain_core.tools import tool
from src.core.logging_config import get_logger
from src.integrations.zendesk.client import get_zendesk_client
from src.integrations.zendesk.service import TicketService

from .templates import template_manager

logger = get_logger("zendesk_tools")


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
# HELPER FUNCTIONS
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


def get_status_display(status: str) -> str:
    """Get emoji + status display."""
    emoji = STATUS_EMOJIS.get(status, "📄")
    return f"{emoji} {status.title()}"


def get_priority_display(priority: str) -> str:
    """Get emoji + priority display."""
    emoji = PRIORITY_EMOJIS.get(priority, "📋")
    return f"{emoji} {priority.title()}"


# ============================================================================
# TOOL FUNCTIONS
# ============================================================================


@tool
async def create_support_ticket(
    customer_message: str,
    ticket_type: str,
    customer_name: str,
    customer_email: str,
    priority: str = "normal",
    conversation_context: str = "",
) -> str:
    """
    Create a Zendesk support ticket for customer assistance.

    IMPORTANT: Always collect customer name and email before using this tool.
    If you don't have this information, ask the customer for it first.

    Use this tool when customers need help that requires follow-up or escalation.

    Args:
        customer_message: The customer's message describing their issue
        ticket_type: Type of support - 'billing', 'technical', 'cancellation', or 'general'
        customer_name: Customer's full name (REQUIRED)
        customer_email: Customer's email address for follow-up (REQUIRED)
        priority: Priority level - 'low', 'normal', 'high', or 'urgent'
        conversation_context: Additional context from the conversation

    Returns:
        Confirmation message with ticket ID and next steps, or request for missing info
    """
    try:
        is_valid, error_msg = validate_customer_info(
            customer_name, customer_email, ticket_type="support"
        )
        if not is_valid:
            return error_msg

        customer_info = format_customer_info(customer_name, customer_email)

        request_summary = customer_message
        if conversation_context:
            request_summary += f"\n\nAdditional Context:\n{conversation_context}"

        ticket_data = template_manager.get_support_ticket_data(
            ticket_type=ticket_type,
            customer_info=customer_info,
            request_summary=request_summary,
        )

        final_priority = (
            priority
            if priority in ["low", "normal", "high", "urgent"]
            else ticket_data["priority"]
        )

        async with await get_zendesk_client() as zendesk_client:
            ticket_service = TicketService(zendesk_client)

            created_ticket = await ticket_service.create_ticket(
                subject=ticket_data["subject"],
                description=ticket_data["description"],
                requester_email=customer_email,
                requester_name=customer_name,
                ticket_type=ticket_data["zendesk_type"],
                priority=final_priority,
                tags=ticket_data["tags"],
            )

        return template_manager.get_customer_response(ticket_type, created_ticket.id)

    except Exception as e:
        logger.error(f"Failed to create support ticket: {str(e)}")
        return template_manager.get_error_response("general_error")


@tool
async def create_sales_ticket(
    customer_message: str,
    customer_name: str,
    customer_email: str,
    customer_phone: str = "",
    interest_level: str = "medium",
    conversation_summary: str = "",
) -> str:
    """
    Create a high-priority sales ticket for interested customers.

    IMPORTANT: Always collect customer name, email, and phone before using this tool.
    If you don't have this information, ask the customer for it first.

    Use this tool when customers show interest in purchasing TeleCorp services.

    Args:
        customer_message: Customer's sales inquiry or interest
        customer_name: Customer's full name (REQUIRED)
        customer_email: Customer's email address for follow-up (REQUIRED)
        customer_phone: Customer's phone number for direct contact (RECOMMENDED)
        interest_level: Customer interest level - 'low', 'medium', or 'high'
        conversation_summary: Summary of what the customer is looking for

    Returns:
        Confirmation message optimized for sales follow-up, or request for missing info
    """
    try:
        is_valid, error_msg = validate_customer_info(
            customer_name, customer_email, customer_phone, ticket_type="sales"
        )
        if not is_valid:
            return error_msg

        customer_info = format_customer_info(
            customer_name, customer_email, customer_phone
        )
        sales_context = build_sales_context(interest_level, conversation_summary)

        ticket_data = template_manager.get_sales_ticket_data(
            customer_info=customer_info,
            request_summary=customer_message,
            sales_context=sales_context,
            interest_level=interest_level,
        )

        async with await get_zendesk_client() as zendesk_client:
            ticket_service = TicketService(zendesk_client)

            created_ticket = await ticket_service.create_ticket(
                subject=ticket_data["subject"],
                description=ticket_data["description"],
                requester_email=customer_email,
                requester_name=customer_name,
                ticket_type=ticket_data["zendesk_type"],
                priority=ticket_data["priority"],
                tags=ticket_data["tags"],
            )

        return template_manager.get_customer_response("sales", created_ticket.id)

    except Exception as e:
        logger.error(f"Failed to create sales ticket: {str(e)}")
        return template_manager.get_error_response("sales_error")


@tool
async def get_user_tickets(customer_email: str) -> str:
    """
    Get existing Zendesk tickets for a customer by email address.

    Use this tool to check if a TeleCorp customer has existing support tickets
    that they might want to discuss or follow up on.

    Args:
        customer_email: Customer's email address to search for tickets

    Returns:
        Formatted list of customer tickets with IDs, subjects, and status,
        or message if no tickets found
    """
    try:
        if not customer_email:
            return "I'll need your email address to look up your tickets. Could you please provide your email?"

        async with await get_zendesk_client() as zendesk_client:
            ticket_service = TicketService(zendesk_client)
            tickets = await ticket_service.search_tickets_by_email(customer_email)

        if not tickets:
            return f"I didn't find any existing tickets for {customer_email}. You appear to be a new customer or haven't contacted support before. How can I help you today?"

        customer_visible_tickets = filter_customer_visible_tickets(tickets)

        if not customer_visible_tickets:
            return f"I didn't find any existing support tickets for {customer_email}. How can I help you today?"

        ticket_display = format_ticket_list(customer_visible_tickets)

        response = f"""Great! I found your account. You have {len(customer_visible_tickets)} support ticket(s) with TeleCorp:

{ticket_display}

Would you like to:
• Discuss one of these existing tickets (just tell me the number)
• Create a new support request
• Ask questions about your service

Which would you prefer?"""

        return response

    except Exception as e:
        logger.error(f"Failed to get user tickets: {str(e)}")
        return "I'm having trouble accessing your ticket history right now. Let me help you with your current question instead. What can I assist you with today?"


@tool
async def get_ticket_details(ticket_id: str, customer_email: str) -> str:
    """
    Get detailed information about a specific ticket.

    Use this tool when a customer wants to discuss a specific ticket
    that was found in their ticket history.

    Args:
        ticket_id: The Zendesk ticket ID to retrieve details for
        customer_email: Customer's email to verify ownership

    Returns:
        Detailed ticket information including description, status, and recent updates
    """
    try:
        if not ticket_id or not customer_email:
            return "I'll need both the ticket ID and your email address to look up the ticket details."

        async with await get_zendesk_client() as zendesk_client:
            ticket_service = TicketService(zendesk_client)
            ticket = await ticket_service.get_ticket_by_id(int(ticket_id))

            if not ticket:
                return f"I couldn't find ticket #{ticket_id}. Please double-check the ticket number."

        status_display = get_status_display(ticket.status)
        priority_display = get_priority_display(ticket.priority)

        response = f"""Here are the details for Ticket #{ticket.id}:

**Subject:** {ticket.subject}
**Status:** {status_display}
**Priority:** {priority_display}
**Created:** {ticket.created_at.strftime('%B %d, %Y at %I:%M %p') if ticket.created_at else 'Unknown'}

**Original Request:**
{ticket.description[:500] if ticket.description else 'No description available'}{"..." if ticket.description and len(ticket.description) > 500 else ""}

How can I help you with this ticket? Would you like to:
• Check for updates on this issue
• Add more information
• Ask questions about the resolution
• Something else?"""

        return response

    except Exception as e:
        logger.error(f"Failed to get ticket details for {ticket_id}: {str(e)}")
        return f"I'm having trouble accessing the details for ticket #{ticket_id}. Let me know what specific question you have about this ticket and I'll do my best to help."


# Export the tools
zendesk_tools_clean = [
    create_support_ticket,
    create_sales_ticket,
    get_user_tickets,
    get_ticket_details,
]
