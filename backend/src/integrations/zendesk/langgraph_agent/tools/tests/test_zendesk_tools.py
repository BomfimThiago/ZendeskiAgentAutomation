"""
Unit tests for Zendesk ticket creation tools.

These tests verify ticket operations work correctly with mocked Zendesk client.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.integrations.zendesk.models import ZendeskTicket

from src.integrations.zendesk.langgraph_agent.tools.zendesk_tools import (
    create_support_ticket,
    create_sales_ticket,
    get_user_tickets,
    get_ticket_details,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestCreateSupportTicket:
    """Test support ticket creation tool."""

    async def test_create_support_ticket_validates_customer_info(self):
        """Test that tool validates customer info before creating ticket."""
        # Missing email should trigger validation error
        result = await create_support_ticket.ainvoke({
            "customer_message": "I need help",
            "ticket_type": "technical",
            "customer_name": "John Doe",
            "customer_email": "",  # Empty email
            "priority": "normal"
        })

        assert "email" in result.lower()
        assert "provide" in result.lower() or "need" in result.lower()

    async def test_create_support_ticket_validates_customer_name(self):
        """Test that tool validates customer name."""
        result = await create_support_ticket.ainvoke({
            "customer_message": "I need help",
            "ticket_type": "technical",
            "customer_name": "",  # Empty name
            "customer_email": "john@example.com",
            "priority": "normal"
        })

        assert "name" in result.lower()
        assert "provide" in result.lower() or "need" in result.lower()

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_create_support_ticket_success(self, mock_get_client):
        """Test successful ticket creation with mocked client."""
        # Mock Zendesk client and ticket service
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_ticket = MagicMock(spec=ZendeskTicket)
        mock_ticket.id = 12345
        mock_ticket.subject = "Technical Support Request"

        mock_service.create_ticket = AsyncMock(return_value=mock_ticket)

        # Mock the context manager
        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await create_support_ticket.ainvoke({
                "customer_message": "My internet is slow",
                "ticket_type": "technical",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "priority": "normal"
            })

            assert "12345" in result
            assert "ticket" in result.lower()
            mock_service.create_ticket.assert_called_once()

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_create_support_ticket_handles_errors(self, mock_get_client):
        """Test that tool handles Zendesk API errors gracefully."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_service.create_ticket = AsyncMock(side_effect=Exception("API Error"))

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await create_support_ticket.ainvoke({
                "customer_message": "I need help",
                "ticket_type": "technical",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "priority": "normal"
            })

            # Should return error message, not crash
            assert "apolog" in result.lower() or "trouble" in result.lower()
            assert "contact" in result.lower() or "call" in result.lower()

    async def test_create_support_ticket_validates_ticket_type(self):
        """Test ticket creation with different ticket types."""
        types_to_test = ["billing", "technical", "cancellation", "general"]

        for ticket_type in types_to_test:
            # Just verify it doesn't crash with different types
            result = await create_support_ticket.ainvoke({
                "customer_message": f"Test {ticket_type} issue",
                "ticket_type": ticket_type,
                "customer_name": "",  # Will trigger validation
                "customer_email": "test@example.com",
                "priority": "normal"
            })
            assert isinstance(result, str)


@pytest.mark.unit
@pytest.mark.asyncio
class TestCreateSalesTicket:
    """Test sales ticket creation tool."""

    async def test_create_sales_ticket_requires_contact_info(self):
        """Test that sales ticket requires name and email."""
        result = await create_sales_ticket.ainvoke({
            "customer_message": "I want to buy internet",
            "customer_name": "",
            "customer_email": "",
            "customer_phone": ""
        })

        assert "email" in result.lower() or "name" in result.lower()
        assert "provide" in result.lower() or "need" in result.lower()

    async def test_create_sales_ticket_phone_recommended(self):
        """Test that phone is recommended for sales tickets."""
        # Without phone, should work but might have message about phone
        result = await create_sales_ticket.ainvoke({
            "customer_message": "I want to buy internet",
            "customer_name": "Jane Doe",
            "customer_email": "jane@example.com",
            "customer_phone": "",  # No phone
            "interest_level": "high"
        })

        # Tool should ask for phone or proceed with warning
        assert isinstance(result, str)

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_create_sales_ticket_success(self, mock_get_client):
        """Test successful sales ticket creation."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_ticket = MagicMock(spec=ZendeskTicket)
        mock_ticket.id = 54321
        mock_ticket.subject = "Sales Inquiry"

        mock_service.create_ticket = AsyncMock(return_value=mock_ticket)

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await create_sales_ticket.ainvoke({
                "customer_message": "I want gigabit internet",
                "customer_name": "Jane Doe",
                "customer_email": "jane@example.com",
                "customer_phone": "+1-555-0123",
                "interest_level": "high",
                "conversation_summary": "Customer interested in fastest plan"
            })

            assert "54321" in result
            assert "ticket" in result.lower()
            mock_service.create_ticket.assert_called_once()

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_create_sales_ticket_handles_errors(self, mock_get_client):
        """Test sales ticket error handling."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_service.create_ticket = AsyncMock(side_effect=Exception("API Error"))

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await create_sales_ticket.ainvoke({
                "customer_message": "I want to buy",
                "customer_name": "Jane Doe",
                "customer_email": "jane@example.com",
                "customer_phone": "+1-555-0123"
            })

            # Should return sales-specific error message
            assert "sales" in result.lower() or "call" in result.lower()


@pytest.mark.unit
@pytest.mark.asyncio
class TestGetUserTickets:
    """Test user ticket retrieval tool."""

    async def test_get_user_tickets_requires_email(self):
        """Test that tool requires email address."""
        result = await get_user_tickets.ainvoke({"customer_email": ""})

        assert "email" in result.lower()
        assert "need" in result.lower() or "provide" in result.lower()

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_get_user_tickets_no_tickets_found(self, mock_get_client):
        """Test response when no tickets found for email."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_service.search_tickets_by_email = AsyncMock(return_value=[])

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await get_user_tickets.ainvoke({"customer_email": "new@example.com"})

            assert "didn't find" in result.lower() or "no" in result.lower()
            assert "new@example.com" in result

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_get_user_tickets_returns_formatted_list(self, mock_get_client):
        """Test that tool returns formatted ticket list."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()

        # Create mock tickets
        mock_ticket1 = MagicMock(spec=ZendeskTicket)
        mock_ticket1.id = 111
        mock_ticket1.subject = "Billing Question"
        mock_ticket1.status = "open"
        mock_ticket1.created_at = None

        mock_ticket2 = MagicMock(spec=ZendeskTicket)
        mock_ticket2.id = 222
        mock_ticket2.subject = "Technical Issue"
        mock_ticket2.status = "pending"
        mock_ticket2.created_at = None

        mock_service.search_tickets_by_email = AsyncMock(return_value=[mock_ticket1, mock_ticket2])

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await get_user_tickets.ainvoke({"customer_email": "existing@example.com"})

            # Should contain ticket IDs
            assert "111" in result or "222" in result
            # Should contain status info
            assert "ticket" in result.lower()
            mock_service.search_tickets_by_email.assert_called_once_with("existing@example.com")

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_get_user_tickets_handles_errors(self, mock_get_client):
        """Test error handling for ticket retrieval."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_service.search_tickets_by_email = AsyncMock(side_effect=Exception("Search failed"))

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await get_user_tickets.ainvoke({"customer_email": "test@example.com"})

            # Should return friendly error message
            assert "trouble" in result.lower() or "unable" in result.lower()
            assert "help" in result.lower() or "assist" in result.lower()


@pytest.mark.unit
@pytest.mark.asyncio
class TestGetTicketDetails:
    """Test ticket details retrieval tool."""

    async def test_get_ticket_details_requires_params(self):
        """Test that tool requires ticket ID and email."""
        result = await get_ticket_details.ainvoke({
            "ticket_id": "",
            "customer_email": ""
        })

        assert "need" in result.lower() or "require" in result.lower()

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_get_ticket_details_success(self, mock_get_client):
        """Test successful ticket details retrieval."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()

        mock_ticket = MagicMock(spec=ZendeskTicket)
        mock_ticket.id = 999
        mock_ticket.subject = "My Issue"
        mock_ticket.status = "open"
        mock_ticket.priority = "normal"
        mock_ticket.description = "Detailed description of the issue"
        mock_ticket.created_at = None

        mock_service.get_ticket_by_id = AsyncMock(return_value=mock_ticket)

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await get_ticket_details.ainvoke({
                "ticket_id": "999",
                "customer_email": "test@example.com"
            })

            assert "999" in result
            assert "My Issue" in result
            mock_service.get_ticket_by_id.assert_called_once_with(999)

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_get_ticket_details_not_found(self, mock_get_client):
        """Test response when ticket not found."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_service.get_ticket_by_id = AsyncMock(return_value=None)

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await get_ticket_details.ainvoke({
                "ticket_id": "999",
                "customer_email": "test@example.com"
            })

            assert "couldn't find" in result.lower() or "not found" in result.lower()
            assert "999" in result

    @patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.get_zendesk_client')
    async def test_get_ticket_details_handles_errors(self, mock_get_client):
        """Test error handling for ticket details."""
        mock_client = AsyncMock()
        mock_service = AsyncMock()
        mock_service.get_ticket_by_id = AsyncMock(side_effect=Exception("Retrieval failed"))

        mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

        with patch('src.integrations.zendesk.langgraph_agent.tools.zendesk_tools.TicketService', return_value=mock_service):
            result = await get_ticket_details.ainvoke({
                "ticket_id": "999",
                "customer_email": "test@example.com"
            })

            assert "trouble" in result.lower() or "unable" in result.lower()
            assert "999" in result


@pytest.mark.unit
class TestToolConfiguration:
    """Test that tools are properly configured."""

    def test_all_tools_are_async(self):
        """Test that ticket tools support async invocation."""
        tools = [
            create_support_ticket,
            create_sales_ticket,
            get_user_tickets,
            get_ticket_details
        ]

        for tool in tools:
            assert hasattr(tool, 'ainvoke'), f"{tool.name} should have ainvoke method"

    def test_tools_have_proper_metadata(self):
        """Test that all tools have names and descriptions."""
        tools = [
            create_support_ticket,
            create_sales_ticket,
            get_user_tickets,
            get_ticket_details
        ]

        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert len(tool.name) > 0
            assert len(tool.description) > 20  # Should have meaningful description
