"""
Clean and simple Zendesk ticket creation tools for TeleCorp LangGraph agents.

This module provides easy-to-understand tools for creating Zendesk tickets
using the existing Zendesk service layer and organized templates.
"""

from typing import Optional
from langchain_core.tools import tool
from src.core.logging_config import get_logger
from src.integrations.zendesk.client import get_zendesk_client
from src.integrations.zendesk.service import TicketService

from .templates import template_manager

logger = get_logger("zendesk_tools")


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
        # Validate required information
        if not customer_name or customer_name == "TeleCorp Customer":
            return """I'd be happy to create a support ticket for you! To ensure our team can follow up properly, I'll need to get some information from you first.

Could you please provide:
• Your full name
• Your email address

Once I have this information, I'll create your support ticket right away."""

        if not customer_email:
            return f"""Thanks, {customer_name}! I have your name, but I'll also need your email address so our support team can follow up with you directly.

Could you please provide your email address? Once I have that, I'll create your support ticket immediately."""
        # Prepare customer and request data
        customer_info = f"Name: {customer_name}"
        if customer_email:
            customer_info += f", Email: {customer_email}"

        request_summary = customer_message
        if conversation_context:
            request_summary += f"\n\nAdditional Context:\n{conversation_context}"

        # Get complete ticket data from template manager
        ticket_data = template_manager.get_support_ticket_data(
            ticket_type=ticket_type,
            customer_info=customer_info,
            request_summary=request_summary,
        )

        # Validate priority or use default from template
        final_priority = (
            priority
            if priority in ["low", "normal", "high", "urgent"]
            else ticket_data["priority"]
        )

        # Use existing Zendesk service to create ticket
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

        # Return appropriate response message
        return template_manager.get_customer_response(ticket_type, created_ticket.id)

    except Exception as e:
        logger.error(f"Failed to create support ticket: {str(e)}")
        return template_manager.get_error_response("general_error")


@tool
async def create_sales_ticket(
    customer_message: str,
    customer_name: str,
    customer_email: str,
    interest_level: str = "medium",
    conversation_summary: str = "",
) -> str:
    """
    Create a high-priority sales ticket for interested customers.

    IMPORTANT: Always collect customer name and email before using this tool.
    If you don't have this information, ask the customer for it first.

    Use this tool when customers show interest in purchasing TeleCorp services.

    Args:
        customer_message: Customer's sales inquiry or interest
        customer_name: Customer's full name (REQUIRED)
        customer_email: Customer's email address for follow-up (REQUIRED)
        interest_level: Customer interest level - 'low', 'medium', or 'high'
        conversation_summary: Summary of what the customer is looking for

    Returns:
        Confirmation message optimized for sales follow-up, or request for missing info
    """
    try:
        # Validate required information
        if not customer_name or customer_name == "Prospective Customer":
            return """I'm excited to help you with TeleCorp services! To ensure our sales team can provide you with personalized assistance and follow up properly, I'll need to get some information from you first.

Could you please provide:
• Your full name
• Your email address

Once I have this information, I'll prioritize your sales inquiry and get you connected with our best specialists!"""

        if not customer_email:
            return f"""Great to meet you, {customer_name}! I'm excited to help you find the perfect TeleCorp solution. To ensure our sales team can follow up with personalized pricing and options, I'll need your email address.

Could you please provide your email? Once I have that, I'll create a high-priority sales ticket and you'll hear from our specialists within hours!"""
        # Prepare sales context
        sales_context = f"""
            Interest Level: {interest_level}
            Conversation Summary: {conversation_summary}

            Sales Notes:
            - Customer engaged with AI agent about TeleCorp services
            - Qualified lead requiring sales follow-up
            - Opportunity for immediate conversion
        """

        # Prepare customer and request data
        customer_info = f"Name: {customer_name}"
        if customer_email:
            customer_info += f", Email: {customer_email}"

        # Get complete ticket data from template manager
        ticket_data = template_manager.get_sales_ticket_data(
            customer_info=customer_info,
            request_summary=customer_message,
            sales_context=sales_context,
            interest_level=interest_level,
        )

        # Use existing Zendesk service to create ticket
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

        # Return sales-specific response message
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

        # Use existing Zendesk service to search for tickets by email
        async with await get_zendesk_client() as zendesk_client:
            ticket_service = TicketService(zendesk_client)

            # Use efficient search method instead of filtering all tickets
            tickets = await ticket_service.search_tickets_by_email(customer_email)

        if not tickets:
            return f"I didn't find any existing tickets for {customer_email}. You appear to be a new customer or haven't contacted support before. How can I help you today?"

        # Format tickets for presentation
        ticket_list = []
        for i, ticket in enumerate(tickets[:5], 1):  # Show max 5 recent tickets
            status_emoji = {
                'new': '🆕',
                'open': '📂',
                'pending': '⏳',
                'hold': '⏸️',
                'solved': '✅',
                'closed': '📁'
            }.get(ticket.status, '📄')

            ticket_list.append(
                f"{i}. {status_emoji} Ticket #{ticket.id}: {ticket.subject} ({ticket.status.upper()})"
            )

        if len(tickets) > 5:
            ticket_list.append(f"... and {len(tickets) - 5} more tickets")

        response = f"""Great! I found your account. You have {len(tickets)} ticket(s) with TeleCorp:

{chr(10).join(ticket_list)}

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

        # Use existing Zendesk service to get ticket details
        async with await get_zendesk_client() as zendesk_client:
            ticket_service = TicketService(zendesk_client)

            # Get the specific ticket
            ticket = await ticket_service.get_ticket_by_id(int(ticket_id))

            if not ticket:
                return f"I couldn't find ticket #{ticket_id}. Please double-check the ticket number."

        # Format ticket details for presentation
        status_emoji = {
            'new': '🆕 New',
            'open': '📂 Open',
            'pending': '⏳ Pending',
            'hold': '⏸️ On Hold',
            'solved': '✅ Solved',
            'closed': '📁 Closed'
        }.get(ticket.status, f'📄 {ticket.status.title()}')

        priority_emoji = {
            'low': '🔵 Low',
            'normal': '🟢 Normal',
            'high': '🟡 High',
            'urgent': '🔴 Urgent'
        }.get(ticket.priority, f'📋 {ticket.priority.title()}')

        response = f"""Here are the details for Ticket #{ticket.id}:

**Subject:** {ticket.subject}
**Status:** {status_emoji}
**Priority:** {priority_emoji}
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
zendesk_tools_clean = [create_support_ticket, create_sales_ticket, get_user_tickets, get_ticket_details]
