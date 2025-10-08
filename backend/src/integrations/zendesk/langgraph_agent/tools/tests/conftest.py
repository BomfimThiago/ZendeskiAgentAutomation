"""Fixtures for tool tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


@pytest.fixture
def mock_get_zendesk_client():
    """Mock get_zendesk_client context manager."""
    mock_client = AsyncMock()
    mock_client.create_ticket = AsyncMock()
    mock_client.search_tickets_by_email = AsyncMock()
    mock_client.get_ticket_by_id = AsyncMock()

    # Mock the context manager
    async def async_context_manager():
        return mock_client

    with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client') as mock:
        mock.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock.return_value.__aexit__ = AsyncMock(return_value=None)
        yield mock_client


@pytest.fixture
def sample_customer_info():
    """Sample customer information for testing."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123"
    }


@pytest.fixture
def mock_knowledge_base_path(tmp_path):
    """Create a temporary knowledge base directory with sample files."""
    kb_dir = tmp_path / "myawesomefakecompanyBaseKnowledge"
    kb_dir.mkdir()

    # Create sample files
    (kb_dir / "MyAwesomeFakeCompany Company Story.txt").write_text(
        "MyAwesomeFakeCompany was founded in 2018..."
    )

    plans_dir = kb_dir / "plans"
    plans_dir.mkdir()
    (plans_dir / "internet_plans.txt").write_text(
        "Basic: 25 Mbps - $29.99\nStandard: 100 Mbps - $49.99"
    )

    faq_dir = kb_dir / "FAQ"
    faq_dir.mkdir()
    (faq_dir / "general_faq.txt").write_text(
        "Q: How do I pay my bill?\nA: Visit our website..."
    )

    return kb_dir
