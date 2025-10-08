"""
Customer response message templates for ticket confirmations.

This module contains the templates for messages sent back to customers
after creating different types of support tickets.
"""


def _billing_response() -> str:
    """Billing support ticket confirmation message."""
    return """
    I've created a billing support ticket #{ticket_id} to address your concern.

    Our billing specialists will review your account and contact you within
    48 hours to resolve this issue. Please keep ticket #{ticket_id} for your records.

    For urgent billing matters, you can also call our billing support at 1-800-AWESOME-COMPANY.
    """.strip()


def _technical_response() -> str:
    """Technical support ticket confirmation message."""
    return """
    I've created a technical support ticket #{ticket_id} for your issue.

    Our technical team will investigate and contact you with troubleshooting steps
    or schedule a service visit if needed. We'll aim to resolve this within 24-48 hours.

    For immediate technical assistance, you can also call 1-800-TECH-TEL.
    """.strip()


def _cancellation_response() -> str:
    """Cancellation request ticket confirmation message."""
    return """
    I've created ticket #{ticket_id} for your cancellation request.

    Our customer retention team will reach out within 24 hours to discuss your account
    and explore options that might work better for you. We value your business and want
    to make sure we're meeting your needs.

    You can reference ticket #{ticket_id} for this request.
    """.strip()


def _general_response() -> str:
    """General inquiry ticket confirmation message."""
    return """
    I've created ticket #{ticket_id} to ensure you get the most accurate information.

    Our customer service team will follow up with detailed information within 24 hours.
    Please reference ticket #{ticket_id} in any future communications.

    Is there anything else I can help you with today?
    """.strip()


def _sales_response() -> str:
    """Sales inquiry ticket confirmation message."""
    return """
    Excellent! I've prioritized your sales inquiry as ticket #{ticket_id}.

    A MyAwesomeFakeCompany sales specialist will contact you within 4 hours to discuss your
    specific needs and provide personalized pricing options. We have some fantastic
    promotional offers available right now!

    While you wait, is there anything specific about our plans or services you'd
    like me to explain further?

    Reference: Sales Ticket #{ticket_id}
    """.strip()


# Customer response templates for support tickets
CUSTOMER_RESPONSE_TEMPLATES = {
    "billing": _billing_response(),
    "technical": _technical_response(),
    "cancellation": _cancellation_response(),
    "general": _general_response(),
    "sales": _sales_response(),
}


def _general_error_response() -> str:
    """General error message when ticket creation fails."""
    return """
    I apologize, but I'm having trouble creating a support ticket right now.

    Please contact MyAwesomeFakeCompany customer service directly:
    • General Support: 1-800-AWESOME-COMPANY
    • Technical Support: 1-800-TECH-TEL
    • Sales Inquiries: 1-800-NEW-PLAN
    • Billing Questions: 1-800-AWESOME-COMPANY

    Our team is available 24/7 to assist you.
    """.strip()


def _sales_error_response() -> str:
    """Sales-specific error message when ticket creation fails."""
    return """
    I apologize for the technical difficulty. For immediate sales assistance,
    please contact our sales team directly at 1-800-NEW-PLAN.

    Our sales specialists are available to discuss plans, pricing, and current
    promotions. They can typically provide quotes within minutes of your call!
    """.strip()


# Error response templates
ERROR_RESPONSE_TEMPLATES = {
    "general_error": _general_error_response(),
    "sales_error": _sales_error_response(),
}


def get_customer_response(response_type: str, ticket_id: int) -> str:
    """
    Get customer response message for a specific ticket type.

    Args:
        response_type: Type of response (billing, technical, cancellation, general, sales)
        ticket_id: The created ticket ID number

    Returns:
        Formatted customer response message with ticket ID
    """
    template = CUSTOMER_RESPONSE_TEMPLATES.get(
        response_type.lower(), CUSTOMER_RESPONSE_TEMPLATES["general"]
    )
    return template.format(ticket_id=ticket_id)


def get_error_response(error_type: str = "general_error") -> str:
    """
    Get error response message when ticket creation fails.

    Args:
        error_type: Type of error (general_error, sales_error)

    Returns:
        Appropriate error message for the customer
    """
    return ERROR_RESPONSE_TEMPLATES.get(
        error_type, ERROR_RESPONSE_TEMPLATES["general_error"]
    )
