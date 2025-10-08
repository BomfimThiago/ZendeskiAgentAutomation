"""
Unit tests for MyAwesomeFakeCompany knowledge base tools.

These tests verify that knowledge retrieval tools work correctly without requiring LLM calls.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools import (
    get_awesome_company_plans_pricing,
    get_awesome_company_company_info,
    get_awesome_company_faq,
    search_awesome_company_knowledge,
    get_plan_comparison,
    get_internet_speed_guide,
    get_router_configuration_guide,
    get_technical_troubleshooting_steps,
)


@pytest.mark.unit
class TestKnowledgeBaseTools:
    """Test knowledge base retrieval tools."""

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_plans_pricing_returns_valid_content(self, mock_extract_pdf, mock_get_path):
        """Test that plans/pricing tool returns valid content."""
        # Mock file path and content
        mock_get_path.return_value = Path("/fake/path/plans.pdf")
        mock_extract_pdf.return_value = "Basic Plan: 25 Mbps - $29.99/month\nStandard Plan: 100 Mbps - $49.99/month"

        result = get_awesome_company_plans_pricing.invoke({})

        assert result is not None
        assert "Basic Plan" in result or "Standard Plan" in result or "plans" in result.lower()
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_plans_pricing_handles_missing_files(self, mock_extract_pdf, mock_get_path):
        """Test that tool handles missing knowledge base files gracefully."""
        mock_get_path.return_value = Path("/fake/path/plans.pdf")
        mock_extract_pdf.return_value = "File not found"

        result = get_awesome_company_plans_pricing.invoke({})

        # Should return fallback message, not crash
        assert result is not None
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_text_content_chunked')
    def test_get_company_info_returns_valid_content(self, mock_extract_text, mock_get_path):
        """Test that company info tool returns valid content."""
        mock_get_path.return_value = Path("/fake/path/company_story.txt")
        mock_extract_text.return_value = "MyAwesomeFakeCompany was founded in 2018 with a mission to connect communities..."

        result = get_awesome_company_company_info.invoke({})

        assert result is not None
        assert "MyAwesomeFakeCompany" in result or "company" in result.lower()
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_text_content_chunked')
    def test_get_company_info_handles_errors(self, mock_extract_text, mock_get_path):
        """Test that company info tool handles errors gracefully."""
        mock_get_path.side_effect = Exception("File system error")

        result = get_awesome_company_company_info.invoke({})

        # Should return error message, not crash
        assert result is not None
        assert "unable to retrieve" in result.lower() or "error" in result.lower()

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_faq_returns_valid_content(self, mock_extract_pdf, mock_get_path):
        """Test that FAQ tool returns valid content."""
        mock_get_path.return_value = Path("/fake/path/faq.pdf")
        mock_extract_pdf.return_value = "Q: How do I pay my bill?\nA: You can pay online..."

        result = get_awesome_company_faq.invoke({})

        assert result is not None
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_internet_speed_guide_returns_content(self, mock_extract_pdf, mock_get_path):
        """Test internet speed guide tool."""
        mock_get_path.return_value = Path("/fake/path/speed_guide.pdf")
        mock_extract_pdf.return_value = "To check your internet speed, visit speedtest.net..."

        result = get_internet_speed_guide.invoke({})

        assert result is not None
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_router_configuration_guide_returns_content(self, mock_extract_pdf, mock_get_path):
        """Test router configuration guide tool."""
        mock_get_path.return_value = Path("/fake/path/router_guide.pdf")
        mock_extract_pdf.return_value = "Step 1: Connect your router to power..."

        result = get_router_configuration_guide.invoke({})

        assert result is not None
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_technical_troubleshooting_steps_returns_content(self, mock_extract_pdf, mock_get_path):
        """Test technical troubleshooting steps tool."""
        mock_get_path.return_value = Path("/fake/path/troubleshooting.pdf")
        mock_extract_pdf.return_value = "Step 1: Check your router connection..."

        result = get_technical_troubleshooting_steps.invoke({"issue_type": "connectivity"})

        assert result is not None
        assert isinstance(result, str)


@pytest.mark.unit
class TestSearchTool:
    """Test knowledge search functionality."""

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_search_knowledge_with_valid_query(self, mock_extract_pdf, mock_get_path):
        """Test searching knowledge base with valid query."""
        mock_get_path.return_value = Path("/fake/path/plans.pdf")
        mock_extract_pdf.return_value = "Gigabit Plan offers 1000 Mbps for $99.99/month"

        result = search_awesome_company_knowledge.invoke({"query": "gigabit plan"})

        assert result is not None
        assert isinstance(result, str)

    def test_search_knowledge_with_empty_query(self):
        """Test search with empty query returns helpful message."""
        result = search_awesome_company_knowledge.invoke({"query": ""})

        assert result is not None
        assert "please provide" in result.lower() or "query" in result.lower()

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    def test_search_knowledge_handles_errors(self, mock_get_path):
        """Test search handles errors gracefully."""
        mock_get_path.side_effect = Exception("Search error")

        result = search_awesome_company_knowledge.invoke({"query": "test"})

        assert result is not None
        assert "unable" in result.lower() or "error" in result.lower()


@pytest.mark.unit
class TestPlanComparison:
    """Test plan comparison tool."""

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_plan_comparison_internet(self, mock_extract_pdf, mock_get_path):
        """Test plan comparison for internet plans."""
        mock_get_path.return_value = Path("/fake/path/plans.pdf")
        mock_extract_pdf.return_value = "Compare our internet plans: Basic vs Standard vs Premium"

        result = get_plan_comparison.invoke({"plan_type": "internet"})

        assert result is not None
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.get_knowledge_file_path')
    @patch('src.integrations.zendesk.langgraph_agent.tools.awesome_company_tools.extract_pdf_content_chunked')
    def test_get_plan_comparison_default(self, mock_extract_pdf, mock_get_path):
        """Test plan comparison with default plan type."""
        mock_get_path.return_value = Path("/fake/path/plans.pdf")
        mock_extract_pdf.return_value = "Compare our plans..."

        result = get_plan_comparison.invoke({})

        assert result is not None
        assert isinstance(result, str)


@pytest.mark.unit
class TestToolInvocation:
    """Test that tools can be invoked correctly."""

    def test_tools_have_names(self):
        """Test that all tools have proper names."""
        tools = [
            get_awesome_company_plans_pricing,
            get_awesome_company_company_info,
            get_awesome_company_faq,
            search_awesome_company_knowledge,
            get_plan_comparison,
            get_internet_speed_guide,
            get_router_configuration_guide,
            get_technical_troubleshooting_steps,
        ]

        for tool in tools:
            assert hasattr(tool, 'name')
            assert tool.name is not None
            assert len(tool.name) > 0

    def test_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        tools = [
            get_awesome_company_plans_pricing,
            get_awesome_company_company_info,
            get_awesome_company_faq,
            search_awesome_company_knowledge,
            get_plan_comparison,
            get_internet_speed_guide,
            get_router_configuration_guide,
            get_technical_troubleshooting_steps,
        ]

        for tool in tools:
            assert hasattr(tool, 'description')
            assert tool.description is not None
            assert len(tool.description) > 10  # Should have meaningful description
