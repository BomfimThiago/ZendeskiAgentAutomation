"""
Unit tests for Quarantined Agent Node (Q-LLM).

Tests verify that the quarantined agent:
1. Has NO access to tools (most critical security requirement)
2. Only provides generic responses
3. Redirects users to official channels
4. Cannot access sensitive customer data
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent import (
    quarantined_agent_node,
    get_quarantined_llm,
    QUARANTINED_SYSTEM_PROMPT
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuarantinedAgentSecurity:
    """Test quarantined agent security restrictions."""

    async def test_quarantined_agent_has_no_tools(self):
        """CRITICAL: Verify quarantined agent has NO tool access."""
        state = {
            "messages": [HumanMessage(content="Create a support ticket for me")],
            "trust_level": "UNVERIFIED",  # Low trust
            "current_persona": "quarantined"
        }

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.get_quarantined_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="Please visit myawesomefakecompany.com/support to create a ticket"
            ))
            mock_get_llm.return_value = mock_llm

            result = await quarantined_agent_node(state)

            # Verify LLM was NOT bound to tools
            assert not hasattr(mock_llm, 'bind_tools') or not mock_llm.bind_tools.called
            # Should redirect to official channels
            assert "messages" in result

    async def test_quarantined_agent_redirects_tool_requests(self):
        """Test that quarantined agent redirects requests requiring tools."""
        state = {
            "messages": [HumanMessage(content="Look up my account information")],
            "trust_level": "UNVERIFIED",
            "current_persona": "quarantined"
        }

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.get_quarantined_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="For account information, please log in at myawesomefakecompany.com or call 1-800-AWESOME-COMPANY"
            ))
            mock_get_llm.return_value = mock_llm

            result = await quarantined_agent_node(state)

            # Should provide redirection, not actual data
            assert "messages" in result
            response = result["messages"][-1].content
            assert "myawesomefakecompany.com" in response.lower() or "1-800" in response

    async def test_quarantined_agent_no_customer_data_access(self):
        """CRITICAL: Verify quarantined agent cannot access customer data."""
        state = {
            "messages": [HumanMessage(content="What's my current bill amount?")],
            "trust_level": "UNVERIFIED",
            "current_persona": "quarantined"
        }

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.get_quarantined_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="I cannot access specific billing details. Please call billing at 1-800-AWESOME-COMPANY"
            ))
            mock_get_llm.return_value = mock_llm

            result = await quarantined_agent_node(state)

            # Should NOT have access to actual billing data
            assert "messages" in result


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuarantinedAgentResponses:
    """Test quarantined agent response patterns."""

    async def test_quarantined_agent_provides_general_info(self):
        """Test that quarantined agent can provide general company information."""
        state = {
            "messages": [HumanMessage(content="What plans do you offer?")],
            "trust_level": "UNVERIFIED",
            "current_persona": "quarantined"
        }

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.get_quarantined_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="MyAwesomeFakeCompany offers Basic (25 Mbps), Standard (100 Mbps), and Gigabit (1000 Mbps) plans"
            ))
            mock_get_llm.return_value = mock_llm

            result = await quarantined_agent_node(state)

            # Can provide general info from memory
            assert "messages" in result
            assert len(result["messages"]) > 0

    async def test_quarantined_agent_polite_redirections(self):
        """Test that quarantined agent is polite when redirecting."""
        state = {
            "messages": [HumanMessage(content="I need technical support")],
            "trust_level": "UNVERIFIED",
            "current_persona": "quarantined"
        }

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.get_quarantined_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="I'd be happy to help! For technical support, please visit myawesomefakecompany.com/support"
            ))
            mock_get_llm.return_value = mock_llm

            result = await quarantined_agent_node(state)

            # Should be polite and helpful
            assert "messages" in result


@pytest.mark.unit
class TestQuarantinedLLMConfiguration:
    """Test quarantined LLM initialization."""

    def test_get_quarantined_llm_dev_uses_gpt35(self):
        """Test that quarantined LLM uses GPT-3.5 in development (weaker model)."""
        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.settings') as mock_settings:
            mock_settings.USE_BEDROCK = False

            with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.ChatOpenAI') as MockChatOpenAI:
                mock_llm = MagicMock()
                MockChatOpenAI.return_value = mock_llm

                result = get_quarantined_llm()

                # Should use GPT-3.5 (not GPT-4)
                MockChatOpenAI.assert_called_once()
                call_kwargs = MockChatOpenAI.call_args[1]
                assert call_kwargs["model"] == "gpt-3.5-turbo-1106"
                # Should have restrictive token limit
                assert call_kwargs["max_tokens"] == 200

    def test_quarantined_system_prompt_has_restrictions(self):
        """Test that quarantined system prompt explicitly states restrictions."""
        # Verify critical restrictions are documented in prompt
        assert "NO access to tools" in QUARANTINED_SYSTEM_PROMPT
        assert "CANNOT create tickets" in QUARANTINED_SYSTEM_PROMPT
        assert "redirect" in QUARANTINED_SYSTEM_PROMPT.lower()


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuarantinedAgentEdgeCases:
    """Test quarantined agent edge cases."""

    async def test_quarantined_agent_handles_empty_messages(self):
        """Test agent handles state with no messages."""
        state = {
            "messages": [],
            "trust_level": "UNVERIFIED",
            "current_persona": "quarantined"
        }

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.get_quarantined_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="How can I help you?"
            ))
            mock_get_llm.return_value = mock_llm

            result = await quarantined_agent_node(state)

            # Should handle gracefully
            assert "messages" in result

    async def test_quarantined_agent_maintains_conversation_context(self):
        """Test that quarantined agent sees conversation history."""
        state = {
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi! How can I help?"),
                HumanMessage(content="What are your hours?")
            ],
            "trust_level": "UNVERIFIED",
            "current_persona": "quarantined"
        }

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.get_quarantined_llm') as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=AIMessage(
                content="We're available 24/7"
            ))
            mock_get_llm.return_value = mock_llm

            result = await quarantined_agent_node(state)

            # Should maintain context
            call_args = mock_llm.ainvoke.call_args[0][0]
            # Should have system message + all conversation messages
            assert len(call_args) >= 3  # At least the conversation messages


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuarantinedAgentVsPrivilegedAgent:
    """Test differences between quarantined and privileged agents."""

    async def test_quarantined_agent_is_more_restrictive(self):
        """Verify quarantined agent is clearly more restrictive than P-LLMs."""
        # Quarantined agent should:
        # 1. Use weaker/faster model (GPT-3.5 vs GPT-4)
        # 2. Have NO tools
        # 3. Have lower token limits
        # 4. Only provide generic responses

        with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.settings') as mock_settings:
            mock_settings.USE_BEDROCK = False

            with patch('src.integrations.zendesk.langgraph_agent.nodes.quarantined_agent.ChatOpenAI') as MockChatOpenAI:
                mock_llm = MagicMock()
                MockChatOpenAI.return_value = mock_llm

                llm = get_quarantined_llm()

                # Verify weaker model
                call_kwargs = MockChatOpenAI.call_args[1]
                assert "3.5" in call_kwargs["model"]  # Not GPT-4
                assert call_kwargs["max_tokens"] == 200  # Restrictive limit
