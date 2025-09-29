"""
Ticket classification system for TeleCorp customer support.

This module classifies customer intentions and maps them to appropriate
Zendesk ticket types, priorities, and tags for proper routing and handling.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

class TicketIntent(Enum):
    """Customer intent categories for ticket classification."""
    SALES = "sales"  # New service, upgrades, contract inquiries
    BILLING = "billing"  # Billing issues, payment problems, invoice questions
    CANCELLATION = "cancellation"  # Service cancellation requests
    TECHNICAL_SUPPORT = "technical_support"  # Technical issues, outages, equipment problems
    GENERAL_INQUIRY = "general_inquiry"  # General questions, company info

class TicketClassification(BaseModel):
    """Classification result for customer intent."""
    intent: TicketIntent
    zendesk_type: str  # Zendesk ticket type: problem, incident, question, task
    priority: str  # Zendesk priority: low, normal, high, urgent
    tags: List[str]  # Tags for categorization and routing
    subject_prefix: str  # Prefix for ticket subject
    description_template: str  # Template for ticket description


class TeleCorpTicketClassifier:
    """Classifier for TeleCorp customer support tickets."""

    # Classification mapping based on customer intent
    INTENT_MAPPINGS: Dict[TicketIntent, TicketClassification] = {
        TicketIntent.SALES: TicketClassification(
            intent=TicketIntent.SALES,
            zendesk_type="task",
            priority="normal",
            tags=["sales", "new_customer", "revenue_opportunity"],
            subject_prefix="[SALES]",
            description_template="Customer interested in TeleCorp services.\n\nCustomer Details:\n{customer_info}\n\nRequest Summary:\n{request_summary}\n\nNext Steps:\n- Follow up within 24 hours\n- Provide service consultation\n- Send pricing information"
        ),

        TicketIntent.BILLING: TicketClassification(
            intent=TicketIntent.BILLING,
            zendesk_type="problem",
            priority="high",
            tags=["billing", "payment", "customer_service"],
            subject_prefix="[BILLING]",
            description_template="Customer has a billing-related issue.\n\nCustomer Details:\n{customer_info}\n\nBilling Issue:\n{request_summary}\n\nPriority Actions:\n- Review account billing history\n- Investigate payment processing\n- Resolve within 48 hours"
        ),

        TicketIntent.CANCELLATION: TicketClassification(
            intent=TicketIntent.CANCELLATION,
            zendesk_type="task",
            priority="high",
            tags=["cancellation", "retention", "churn_risk"],
            subject_prefix="[RETENTION]",
            description_template="Customer requesting service cancellation.\n\nCustomer Details:\n{customer_info}\n\nCancellation Request:\n{request_summary}\n\nRetention Actions:\n- Understand cancellation reason\n- Offer retention options\n- Process if necessary\n- Schedule follow-up"
        ),

        TicketIntent.TECHNICAL_SUPPORT: TicketClassification(
            intent=TicketIntent.TECHNICAL_SUPPORT,
            zendesk_type="incident",
            priority="normal",
            tags=["technical", "support", "troubleshooting"],
            subject_prefix="[TECH]",
            description_template="Customer experiencing technical issues.\n\nCustomer Details:\n{customer_info}\n\nTechnical Issue:\n{request_summary}\n\nTroubleshooting Steps:\n- Diagnose issue remotely\n- Provide step-by-step resolution\n- Escalate to field tech if needed"
        ),

        TicketIntent.GENERAL_INQUIRY: TicketClassification(
            intent=TicketIntent.GENERAL_INQUIRY,
            zendesk_type="question",
            priority="low",
            tags=["general", "inquiry", "information"],
            subject_prefix="[INFO]",
            description_template="General customer inquiry.\n\nCustomer Details:\n{customer_info}\n\nInquiry:\n{request_summary}\n\nResponse Actions:\n- Provide accurate information\n- Route to appropriate department if needed"
        )
    }

    # Keywords for intent classification
    INTENT_KEYWORDS = {
        TicketIntent.SALES: [
            "buy", "purchase", "sign up", "new service", "plan", "package",
            "pricing", "quote", "upgrade", "add service", "contract", "subscribe",
            "interested in", "want to get", "looking for"
        ],

        TicketIntent.BILLING: [
            "bill", "billing", "payment", "charge", "invoice", "refund",
            "overcharge", "credit", "balance", "fee", "cost", "money",
            "pay", "paid", "payment failed", "auto pay", "billing error"
        ],

        TicketIntent.CANCELLATION: [
            "cancel", "cancellation", "disconnect", "terminate", "stop service",
            "end service", "close account", "quit", "leave", "unsubscribe",
            "discontinue"
        ],

        TicketIntent.TECHNICAL_SUPPORT: [
            "not working", "broken", "down", "outage", "slow", "connection",
            "internet", "wifi", "router", "modem", "equipment", "technical",
            "troubleshoot", "fix", "repair", "signal", "speed", "connectivity"
        ]
    }

    def classify_intent(self, message_content: str) -> TicketIntent:
        """
        Classify customer intent based on message content.

        Args:
            message_content: The customer's message content

        Returns:
            TicketIntent enum value
        """
        message_lower = message_content.lower()

        # Score each intent based on keyword matches
        intent_scores = {intent: 0 for intent in TicketIntent}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    intent_scores[intent] += 1

        # Return intent with highest score, default to GENERAL_INQUIRY
        best_intent = max(intent_scores, key=intent_scores.get)

        # If no keywords matched, default to general inquiry
        if intent_scores[best_intent] == 0:
            return TicketIntent.GENERAL_INQUIRY

        return best_intent

    def get_ticket_classification(self, intent: TicketIntent) -> TicketClassification:
        """
        Get ticket classification details for a given intent.

        Args:
            intent: The classified customer intent

        Returns:
            TicketClassification with Zendesk ticket details
        """
        return self.INTENT_MAPPINGS[intent]

    def classify_and_format(
        self,
        message_content: str,
        customer_info: str = "Name and contact details captured from conversation",
        additional_context: str = ""
    ) -> Dict:
        """
        Classify intent and return formatted ticket data for Zendesk.

        Args:
            message_content: Customer's message content
            customer_info: Customer identification information
            additional_context: Additional context from conversation

        Returns:
            Dictionary with formatted ticket data ready for Zendesk API
        """
        intent = self.classify_intent(message_content)
        classification = self.get_ticket_classification(intent)

        # Create request summary combining message and context
        request_summary = message_content
        if additional_context:
            request_summary += f"\n\nAdditional Context:\n{additional_context}"

        # Format description using template
        description = classification.description_template.format(
            customer_info=customer_info,
            request_summary=request_summary
        )

        # Create subject with prefix
        subject = f"{classification.subject_prefix} Customer Support Request"

        return {
            "intent": intent.value,
            "subject": subject,
            "description": description,
            "type": classification.zendesk_type,
            "priority": classification.priority,
            "tags": classification.tags
        }


# Global classifier instance
telecorp_classifier = TeleCorpTicketClassifier()