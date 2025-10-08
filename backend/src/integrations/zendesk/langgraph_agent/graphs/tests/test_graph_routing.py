"""
Unit tests for LangGraph routing logic.

Tests verify that the graph correctly routes based on state,
without actually executing LLM calls.
"""
import pytest
from langgraph.graph import END

from src.integrations.zendesk.langgraph_agent.graphs.awesome_company_graph import (
    should_continue_after_supervisor,
    should_continue_after_intent_extraction,
)


@pytest.mark.unit
class TestSupervisorRouting:
    """Test supervisor conditional routing logic."""

    def test_route_to_support_agent(self):
        """Test supervisor routes to support agent when route_to is 'support'."""
        state = {"route_to": "support"}

        result = should_continue_after_supervisor(state)

        assert result == "support_agent"

    def test_route_to_sales_agent(self):
        """Test supervisor routes to sales agent when route_to is 'sales'."""
        state = {"route_to": "sales"}

        result = should_continue_after_supervisor(state)

        assert result == "sales_agent"

    def test_route_to_billing_agent(self):
        """Test supervisor routes to billing agent when route_to is 'billing'."""
        state = {"route_to": "billing"}

        result = should_continue_after_supervisor(state)

        assert result == "billing_agent"

    def test_route_to_end_when_no_route(self):
        """Test supervisor routes to END when no specific route set."""
        state = {}

        result = should_continue_after_supervisor(state)

        assert result == END

    def test_route_to_end_with_invalid_route(self):
        """Test supervisor routes to END with unrecognized route_to value."""
        state = {"route_to": "unknown_agent"}

        result = should_continue_after_supervisor(state)

        assert result == END


@pytest.mark.unit
class TestIntentExtractionRouting:
    """Test Q-LLM intent extraction routing logic."""

    def test_route_blocked_input_to_sanitization(self):
        """Test that blocked input goes directly to output sanitization."""
        state = {
            "security_blocked": True,
            "structured_intent": {
                "intent": "attack",
                "safety_assessment": "attack"
            }
        }

        result = should_continue_after_intent_extraction(state)

        assert result == "sanitize"

    def test_route_attack_intent_to_quarantined(self):
        """Test that attack intent routes to quarantined agent."""
        state = {
            "security_blocked": False,
            "structured_intent": {
                "intent": "attack",
                "safety_assessment": "attack"
            }
        }

        result = should_continue_after_intent_extraction(state)

        assert result == "quarantined"

    def test_route_suspicious_to_quarantined(self):
        """Test that suspicious input routes to quarantined agent (no tools)."""
        state = {
            "security_blocked": False,
            "structured_intent": {
                "intent": "general",
                "safety_assessment": "suspicious"
            }
        }

        result = should_continue_after_intent_extraction(state)

        assert result == "quarantined"

    def test_route_safe_to_supervisor(self):
        """CRITICAL: Test that safe input routes to P-LLM supervisor."""
        state = {
            "security_blocked": False,
            "structured_intent": {
                "intent": "support",
                "safety_assessment": "safe"
            }
        }

        result = should_continue_after_intent_extraction(state)

        assert result == "supervisor"

    def test_route_safe_sales_to_supervisor(self):
        """Test that safe sales inquiry routes to supervisor."""
        state = {
            "security_blocked": False,
            "structured_intent": {
                "intent": "sales",
                "safety_assessment": "safe"
            }
        }

        result = should_continue_after_intent_extraction(state)

        assert result == "supervisor"

    def test_route_attack_safety_assessment_to_quarantined(self):
        """Test that attack safety_assessment routes to quarantined even if intent is not 'attack'."""
        state = {
            "security_blocked": False,
            "structured_intent": {
                "intent": "general",
                "safety_assessment": "attack"  # Safety assessment overrides intent
            }
        }

        result = should_continue_after_intent_extraction(state)

        assert result == "quarantined"


@pytest.mark.unit
class TestDualLLMArchitectureRouting:
    """Test that routing enforces Dual-LLM security architecture."""

    def test_all_input_passes_through_intent_extraction_first(self):
        """CRITICAL: Verify routing ensures Q-LLM processes ALL input first."""
        # This is verified by graph structure, not routing logic alone
        # The entry point MUST be intent_extraction, never supervisor or agents directly

        # Test various inputs all route through intent extraction
        test_cases = [
            {
                "security_blocked": False,
                "structured_intent": {"intent": "support", "safety_assessment": "safe"}
            },
            {
                "security_blocked": False,
                "structured_intent": {"intent": "sales", "safety_assessment": "safe"}
            },
            {
                "security_blocked": True,
                "structured_intent": {"intent": "attack", "safety_assessment": "attack"}
            }
        ]

        for state in test_cases:
            # Routing should NEVER bypass intent extraction
            result = should_continue_after_intent_extraction(state)
            assert result in ["supervisor", "quarantined", "sanitize"]

    def test_p_llm_only_accessible_after_safe_assessment(self):
        """CRITICAL: Verify P-LLM (supervisor) only receives safe, structured input."""
        # Only "safe" safety_assessment should route to supervisor (P-LLM)

        # Safe input → supervisor (P-LLM)
        safe_state = {
            "security_blocked": False,
            "structured_intent": {"intent": "support", "safety_assessment": "safe"}
        }
        assert should_continue_after_intent_extraction(safe_state) == "supervisor"

        # Attack → quarantined (Q-LLM, no tools)
        attack_state = {
            "security_blocked": False,
            "structured_intent": {"intent": "attack", "safety_assessment": "attack"}
        }
        assert should_continue_after_intent_extraction(attack_state) == "quarantined"

        # Suspicious → quarantined (Q-LLM, no tools)
        suspicious_state = {
            "security_blocked": False,
            "structured_intent": {"intent": "general", "safety_assessment": "suspicious"}
        }
        assert should_continue_after_intent_extraction(suspicious_state) == "quarantined"


@pytest.mark.unit
class TestRoutingEdgeCases:
    """Test edge cases in routing logic."""

    def test_missing_structured_intent(self):
        """Test routing when structured_intent is missing."""
        state = {"security_blocked": False}

        result = should_continue_after_intent_extraction(state)

        # Should treat missing intent as suspicious
        assert result == "quarantined"

    def test_empty_structured_intent(self):
        """Test routing with empty structured_intent dict."""
        state = {
            "security_blocked": False,
            "structured_intent": {}
        }

        result = should_continue_after_intent_extraction(state)

        # Should treat empty intent as suspicious
        assert result == "quarantined"

    def test_missing_safety_assessment(self):
        """Test routing when safety_assessment is missing."""
        state = {
            "security_blocked": False,
            "structured_intent": {"intent": "support"}  # No safety_assessment
        }

        result = should_continue_after_intent_extraction(state)

        # Should default to suspicious and route to quarantined
        assert result == "quarantined"

    def test_security_blocked_overrides_safe_assessment(self):
        """Test that security_blocked=True always routes to sanitization."""
        state = {
            "security_blocked": True,  # BLOCKED
            "structured_intent": {
                "intent": "support",
                "safety_assessment": "safe"  # Contradictory - should prioritize blocked
            }
        }

        result = should_continue_after_intent_extraction(state)

        # security_blocked should take precedence
        assert result == "sanitize"


@pytest.mark.unit
class TestRoutingCoverage:
    """Test all possible routing paths are covered."""

    def test_all_supervisor_routes_covered(self):
        """Test that all supervisor routing paths are covered."""
        # All possible routes from supervisor
        routes = ["support", "sales", "billing", None, "unknown"]
        expected_results = [
            "support_agent",
            "sales_agent",
            "billing_agent",
            END,
            END
        ]

        for route, expected in zip(routes, expected_results):
            state = {"route_to": route} if route else {}
            result = should_continue_after_supervisor(state)
            assert result == expected, f"Failed for route: {route}"

    def test_all_intent_extraction_routes_covered(self):
        """Test that all intent extraction routing paths are covered."""
        # Test cases covering all paths
        test_cases = [
            # (state, expected_route, description)
            (
                {"security_blocked": True, "structured_intent": {}},
                "sanitize",
                "Blocked input"
            ),
            (
                {
                    "security_blocked": False,
                    "structured_intent": {"intent": "attack", "safety_assessment": "attack"}
                },
                "quarantined",
                "Attack intent"
            ),
            (
                {
                    "security_blocked": False,
                    "structured_intent": {"intent": "general", "safety_assessment": "suspicious"}
                },
                "quarantined",
                "Suspicious assessment"
            ),
            (
                {
                    "security_blocked": False,
                    "structured_intent": {"intent": "support", "safety_assessment": "safe"}
                },
                "supervisor",
                "Safe input"
            ),
        ]

        for state, expected, description in test_cases:
            result = should_continue_after_intent_extraction(state)
            assert result == expected, f"Failed for: {description}"
