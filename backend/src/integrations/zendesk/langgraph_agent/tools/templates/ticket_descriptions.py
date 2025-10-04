"""
Ticket description templates for Zendesk tickets.

This module contains the templates used to format ticket descriptions
for different types of support requests.
"""


def _billing_template() -> str:
    """Billing support ticket description template."""
    return """
    Customer has a billing-related issue.

    Customer Details:
    {customer_info}

    Billing Issue:
    {request_summary}

    Priority Actions:
    • Review account billing history
    • Investigate payment processing
    • Resolve within 48 hours
    """.strip()


def _technical_template() -> str:
    """Technical support ticket description template."""
    return """
    Customer experiencing technical issues.

    Customer Details:
    {customer_info}

    Technical Issue:
    {request_summary}

    Troubleshooting Steps:
    • Diagnose issue remotely
    • Provide step-by-step resolution
    • Escalate to field tech if needed
    """.strip()


def _cancellation_template() -> str:
    """Cancellation request ticket description template."""
    return """
    Customer requesting service cancellation.

    Customer Details:
    {customer_info}

    Cancellation Request:
    {request_summary}

    Retention Actions:
    • Understand cancellation reason
    • Offer retention options
    • Process if necessary
    • Schedule follow-up
    """.strip()


def _general_template() -> str:
    """General inquiry ticket description template."""
    return """
    General customer inquiry.

    Customer Details:
    {customer_info}

    Inquiry:
    {request_summary}

    Response Actions:
    • Provide accurate information
    • Route to appropriate department if needed
    """.strip()


# Support ticket description templates
SUPPORT_DESCRIPTION_TEMPLATES = {
    "billing": _billing_template(),
    "technical": _technical_template(),
    "cancellation": _cancellation_template(),
    "general": _general_template(),
}


def _sales_template() -> str:
    """Sales inquiry ticket description template."""
    return """
    Customer interested in TeleCorp services.

    Customer Details:
    {customer_info}

    Request Summary:
    {request_summary}

    Sales Context:
    {sales_context}

    Next Steps:
    • Follow up within 24 hours
    • Provide service consultation
    • Send pricing information
    • Schedule demo if requested
    """.strip()


# Sales ticket description template
SALES_DESCRIPTION_TEMPLATE = _sales_template()


def format_support_description(
    ticket_type: str, customer_info: str, request_summary: str
) -> str:
    """
    Format description for a support ticket.

    Args:
        ticket_type: Type of support ticket (billing, technical, cancellation, general)
        customer_info: Customer contact information
        request_summary: Summary of the customer's request

    Returns:
        Formatted ticket description string
    """
    template = SUPPORT_DESCRIPTION_TEMPLATES.get(
        ticket_type.lower(), SUPPORT_DESCRIPTION_TEMPLATES["general"]
    )
    return template.format(customer_info=customer_info, request_summary=request_summary)


def format_sales_description(
    customer_info: str, request_summary: str, sales_context: str
) -> str:
    """
    Format description for a sales ticket.

    Args:
        customer_info: Customer contact information
        request_summary: Summary of the customer's sales inquiry
        sales_context: Additional sales context and notes

    Returns:
        Formatted sales ticket description string
    """
    return SALES_DESCRIPTION_TEMPLATE.format(
        customer_info=customer_info,
        request_summary=request_summary,
        sales_context=sales_context,
    )
