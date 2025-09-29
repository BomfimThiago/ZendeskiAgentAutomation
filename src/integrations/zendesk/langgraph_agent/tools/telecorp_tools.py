"""
TeleCorp LangGraph Tools

Proper LangGraph tools implementation using @tool decorator for knowledge base access,
plan information, and sales assistance.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import tool

from .knowledge_utils import (
    extract_pdf_content_chunked,
    extract_text_content_chunked,
    get_knowledge_file_path,
)


@tool
def get_telecorp_plans_pricing() -> str:
    """
    Get TeleCorp plans and pricing information for customer inquiries.

    Use this tool when customers ask about:
    - Internet plans and speeds
    - Pricing and costs
    - Available packages
    - Bundle options
    - Promotional offers

    Returns:
        Current TeleCorp plans and pricing information from the knowledge base.
    """
    try:
        plans_files = [
            "TeleCorp Plans and Services - Complete Guide.pdf",
            "Updated Pricing and Products Table - Agent Reference.pdf",
        ]

        plans_content = ""

        for filename in plans_files:
            file_path = get_knowledge_file_path(filename)
            file_content = extract_pdf_content_chunked(file_path, max_chars=500)
            if (
                "Error reading" not in file_content
                and "File not found" not in file_content
            ):
                plans_content += f"From {filename}:\n{file_content}\n\n"

        if plans_content:
            return f"""TeleCorp Plans and Pricing Information:

{plans_content}

SALES GUIDANCE: Present 2-3 specific plans, mention promotions, ask qualifying questions, create urgency, guide to signup.
GENERAL GUIDANCE: Provide overview only, route detailed sales questions to Sales specialist."""

        else:
            return "Unable to access current TeleCorp plans and pricing. Please contact our sales team at 1-800-NEW-PLAN for the latest information."

    except Exception as e:
        return f"Error accessing TeleCorp plans: {str(e)}. Please contact our sales team at 1-800-NEW-PLAN for assistance."


@tool
def get_telecorp_company_info() -> str:
    """
    Get TeleCorp company background and story for customer inquiries.

    Use this tool when customers ask about:
    - Company history and background
    - TeleCorp's mission and values
    - Coverage areas and locations
    - Company achievements and awards

    Returns:
        TeleCorp company information from the knowledge base.
    """
    try:
        company_file = get_knowledge_file_path("TeleCorp Company Story.txt")
        company_content = extract_text_content_chunked(company_file, max_chars=500)

        if (
            "Error reading" not in company_content
            and "File not found" not in company_content
        ):
            return f"""TeleCorp Company Information:

{company_content}

Use this information conversationally to share relevant details about company background, mission, service areas, and what makes TeleCorp different."""

        else:
            return """TeleCorp Company Information:

TeleCorp is a customer-focused telecommunications company founded in 2018, headquartered in Austin, Texas. We're committed to bridging the digital divide with reliable, affordable connectivity across 15 states and growing.

For more detailed company information, please contact us at 1-800-TELECORP."""

    except Exception as e:
        return f"Error accessing TeleCorp company information: {str(e)}. Please contact us at 1-800-TELECORP for more details about our company."


@tool
def get_telecorp_faq() -> str:
    """
    Get TeleCorp frequently asked questions and support information.

    Returns:
        String containing TeleCorp FAQ and common support topics.
    """
    try:
        faq_file = get_knowledge_file_path(
            "TeleCorp Frequently Asked Questions (FAQ).pdf", subfolder="FAQ"
        )
        faq_content = extract_pdf_content_chunked(faq_file, max_chars=500)

        if "Error reading" not in faq_content and "File not found" not in faq_content:
            return f"# TeleCorp FAQ\n\n{faq_content}"
        else:
            return "TeleCorp FAQ not available at this time. Please contact support at 1-800-TELECORP for assistance."

    except Exception as e:
        return f"Error accessing TeleCorp FAQ: {str(e)}"


@tool
def search_telecorp_knowledge(query: str) -> str:
    """
    Search TeleCorp knowledge base for specific information based on a query.

    Args:
        query: The search query or topic to look for in TeleCorp knowledge base

    Returns:
        String containing relevant TeleCorp information based on the query.
    """
    try:
        query_lower = query.lower()

        if any(
            term in query_lower
            for term in ["plan", "price", "pricing", "cost", "package", "service"]
        ):
            return get_telecorp_plans_pricing.invoke({})
        elif any(
            term in query_lower
            for term in ["company", "about", "telecorp", "background", "story"]
        ):
            return get_telecorp_company_info.invoke({})
        elif any(
            term in query_lower
            for term in ["faq", "question", "help", "support", "how to"]
        ):
            return get_telecorp_faq.invoke({})
        else:
            return get_telecorp_plans_pricing.invoke({})

    except Exception as e:
        return f"Error searching TeleCorp knowledge base: {str(e)}"


@tool
def get_plan_comparison(plan_type: str = "internet") -> str:
    """
    Get a comparison of TeleCorp plans for a specific service type.

    Args:
        plan_type: Type of service plan to compare (internet, mobile, bundle, etc.)

    Returns:
        String containing plan comparison information.
    """
    try:
        plans_info = get_telecorp_plans_pricing.invoke({})
        plan_type_lower = plan_type.lower()
        comparison_intro = f"# TeleCorp {plan_type.title()} Plan Comparison\n\n"

        if plan_type_lower == "mobile":
            if "mobile" in plans_info.lower() or "phone" in plans_info.lower():
                return comparison_intro + plans_info
            else:
                return f"# TeleCorp {plan_type.title()} Plan Comparison\n\nMobile plans information not available in current knowledge base. Please contact our sales team at 1-800-NEW-PLAN for mobile plan details."
        else:
            return comparison_intro + plans_info

    except Exception as e:
        return f"Error getting plan comparison for {plan_type}: {str(e)}"


@tool
def get_internet_speed_guide() -> str:
    """
    Get comprehensive internet speed troubleshooting guide.

    Use this tool when customers have:
    - Slow internet speeds
    - Speed test issues
    - Connection quality problems
    - Performance complaints

    Returns:
        Complete guide for internet speed testing and troubleshooting.
    """
    try:
        speed_guide_file = get_knowledge_file_path(
            "How to Check Your Internet Speed - Complete Guide.pdf"
        )
        speed_guide_content = extract_pdf_content_chunked(
            speed_guide_file, max_chars=500
        )

        if (
            "Error reading" not in speed_guide_content
            and "File not found" not in speed_guide_content
        ):
            return f"""Internet Speed Troubleshooting Guide:

{speed_guide_content}

SUPPORT GUIDANCE: Walk customer through testing steps, ask about WiFi/ethernet, device count, provide step-by-step guidance. Create ticket if issue persists."""

        else:
            return "Internet speed guide not available. Please contact technical support at 1-800-TECH-TEL for speed troubleshooting assistance."

    except Exception as e:
        return f"Error accessing internet speed guide: {str(e)}. Please contact technical support at 1-800-TECH-TEL."


@tool
def get_router_configuration_guide() -> str:
    """
    Get comprehensive router configuration and troubleshooting guide.

    Use this tool when customers have:
    - WiFi connection problems
    - Router setup issues
    - Network configuration problems
    - WiFi password issues

    Returns:
        Complete guide for router configuration and troubleshooting.
    """
    try:
        router_guide_file = get_knowledge_file_path(
            "How to Configure Your Router - Complete Guide.pdf"
        )
        router_guide_content = extract_pdf_content_chunked(
            router_guide_file, max_chars=500
        )

        if (
            "Error reading" not in router_guide_content
            and "File not found" not in router_guide_content
        ):
            return f"""Router Configuration Troubleshooting Guide:

{router_guide_content}

SUPPORT GUIDANCE: Ask about router type, lights/colors, power cycle attempts, other device connectivity. Walk through reset steps and configuration. Create ticket if issue persists."""

        else:
            return "Router configuration guide not available. Please contact technical support at 1-800-TECH-TEL for router assistance."

    except Exception as e:
        return f"Error accessing router configuration guide: {str(e)}. Please contact technical support at 1-800-TECH-TEL."


@tool
def get_technical_troubleshooting_steps(issue_type: str) -> str:
    """
    Get specific troubleshooting steps based on the type of technical issue.

    Args:
        issue_type: Type of issue - "speed", "connection", "router", "general"

    Returns:
        Specific troubleshooting steps for the issue type.
    """
    try:
        issue_type_lower = issue_type.lower()

        if "speed" in issue_type_lower:
            return get_internet_speed_guide.invoke({})
        elif any(term in issue_type_lower for term in ["router", "wifi", "connection"]):
            return get_router_configuration_guide.invoke({})
        else:
            # Get general FAQ for other issues
            return get_telecorp_faq.invoke({})

    except Exception as e:
        return f"Error getting troubleshooting steps: {str(e)}. Please contact technical support at 1-800-TECH-TEL."


from .zendesk_tools import zendesk_tools_clean

telecorp_tools = [
    get_telecorp_plans_pricing,
    get_telecorp_company_info,
    get_telecorp_faq,
    search_telecorp_knowledge,
    get_plan_comparison,
    get_internet_speed_guide,
    get_router_configuration_guide,
    get_technical_troubleshooting_steps,
] + zendesk_tools_clean
