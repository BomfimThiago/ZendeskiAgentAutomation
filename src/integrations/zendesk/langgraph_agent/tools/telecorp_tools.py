"""
TeleCorp LangGraph Tools

Proper LangGraph tools implementation using @tool decorator for knowledge base access,
plan information, and sales assistance.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import tool
import pypdf


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
        knowledge_base_path = Path("telecorpBaseKnowledge")
        plans_files = [
            "TeleCorp Plans and Services - Complete Guide.pdf",
            "Updated Pricing and Products Table - Agent Reference.pdf"
        ]

        plans_content = ""

        for filename in plans_files:
            file_path = knowledge_base_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as file:
                        pdf_reader = pypdf.PdfReader(file)
                        for page in pdf_reader.pages:
                            plans_content += page.extract_text() + "\n"
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

        if plans_content:
            # Add guidance for the AI on how to use this information
            return f"""TeleCorp Plans and Pricing Information:

{plans_content}

IMPORTANT FOR SALES ALEX: Use this information to SELL! When used by Sales Alex:
- Present 2-3 specific plan options based on customer needs
- ALWAYS mention promotional pricing and savings
- Highlight competitive advantages and benefits
- Ask qualifying questions (household size, current provider, budget)
- Create urgency with limited-time offers
- Ask which plan they want to start with TODAY
- Guide them to next steps for signup

IMPORTANT FOR GENERAL ALEX: Use this for basic information only
- Provide general overview if asked
- Route sales questions to Sales Alex
- Don't dive deep into pricing details"""

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
        knowledge_base_path = Path("telecorpBaseKnowledge")
        company_file = knowledge_base_path / "TeleCorp Company Story.txt"

        if company_file.exists():
            with open(company_file, 'r', encoding='utf-8') as file:
                company_content = file.read()

            return f"""TeleCorp Company Information:

{company_content}

IMPORTANT: Use this information to help customers understand TeleCorp conversationally. Share relevant details based on their questions about:
- Company background and history
- Our mission and values
- Service areas and coverage
- What makes TeleCorp different
- Contact information when helpful"""

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
        knowledge_base_path = Path("telecorpBaseKnowledge")
        faq_file = knowledge_base_path / "FAQ" / "TeleCorp Frequently Asked Questions (FAQ).pdf"

        if faq_file.exists():
            with open(faq_file, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

                return f"# TeleCorp FAQ\n\n{text}"
        else:
            return "TeleCorp FAQ file not found."

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

        # Determine what type of information is needed
        if any(term in query_lower for term in ['plan', 'price', 'pricing', 'cost', 'package', 'service']):
            return get_telecorp_plans_pricing()
        elif any(term in query_lower for term in ['company', 'about', 'telecorp', 'background', 'story']):
            return get_telecorp_company_info()
        elif any(term in query_lower for term in ['faq', 'question', 'help', 'support', 'how to']):
            return get_telecorp_faq()
        else:
            # Default to plans and pricing for sales-related queries
            return get_telecorp_plans_pricing()

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
        plans_info = get_telecorp_plans_pricing()

        # Extract relevant sections based on plan type
        plan_type_lower = plan_type.lower()

        comparison_intro = f"# TeleCorp {plan_type.title()} Plan Comparison\n\n"

        # Add the full plans info for now - in a real implementation,
        # you would parse and filter the content
        return comparison_intro + plans_info

    except Exception as e:
        return f"Error getting plan comparison for {plan_type}: {str(e)}"


telecorp_tools = [
    get_telecorp_plans_pricing,
    get_telecorp_company_info,
    get_telecorp_faq,
    search_telecorp_knowledge,
    get_plan_comparison
]