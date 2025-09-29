# TeleCorp LangGraph AI Agent

A sales-focused, multi-agent customer support system built with LangGraph that handles customer inquiries, generates leads, and manages support tickets through Zendesk integration.

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Zendesk account with API credentials

### 1. Install uv Package Manager

uv is a fast Python package manager. Install it using one of these methods:

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (using pip):**
```bash
pip install uv
```

### 2. Clone the Repository

```bash
git clone <repository-url>
cd ZendeskiAgentAutomation
```

### 3. Create Virtual Environment

Using uv to create and activate a virtual environment:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
# Install all project dependencies
uv pip install -r requirements.txt

# Or if using pyproject.toml:
uv pip install -e .
```

### 5. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Zendesk Configuration
ZENDESK_SUBDOMAIN=your_subdomain
ZENDESK_EMAIL=your_email@example.com
ZENDESK_API_TOKEN=your_zendesk_api_token
```

### 6. Set Up Knowledge Base

Ensure the knowledge base directory exists with required documents:

```bash
mkdir -p telecorpBaseKnowledge
```

Add your knowledge base files (PDFs, text files) to this directory:
- Plans and pricing documents
- Technical guides
- FAQs
- Company information

### 7. Run the Project

Run the chat frontend to test the AI agent:

```bash
python3 chat_frontend.py
```

Or run from the project root:

```bash
python3 -m src.integrations.zendesk.langgraph_agent.chat_frontend
```

### 8. Verify Setup

The system should:
- Connect to OpenAI API successfully
- Load knowledge base documents
- Initialize LangGraph with all agent nodes
- Start interactive chat interface

If you encounter issues, check:
- Environment variables are set correctly
- Virtual environment is activated
- All dependencies are installed
- Knowledge base directory exists

## Architecture Overview

```
langgraph_agent/
├── config/                    # Configuration settings
│   └── langgraph_config.py   # OpenAI API keys, model settings, company info
│
├── state/                     # State management
│   └── conversation_state.py # Conversation state definition for LangGraph
│
├── nodes/                     # Agent nodes (core business logic)
│   ├── conversation_router.py    # Sales-focused supervisor (default agent)
│   ├── guardrail_node.py         # Security validation (input/output)
│   ├── sales_agent.py             # Sales specialist (lead capture)
│   ├── support_agent.py           # Technical support specialist
│   └── billing_agent.py           # Billing specialist
│
├── graphs/                    # LangGraph workflow
│   └── telecorp_graph.py     # Main graph: validation → supervisor → agents → sanitization
│
├── tools/                     # Tool functions and utilities
│   ├── zendesk_tools.py      # Zendesk ticket creation and management tools
│   ├── telecorp_tools.py     # Knowledge base access tools
│   ├── knowledge_utils.py    # PDF/text extraction utilities
│   ├── utils.py              # Shared helpers (validation, formatting, filtering)
│   └── templates/            # Ticket templates and configurations
│
└── prompts/                   # (Currently empty - prompts inline in agents)
```

## Core Components

### 1. **Conversation Router** (Supervisor Agent)
- **Role**: Sales-focused default agent that handles all conversations
- **Behavior**:
  - Acts as sales representative by default
  - Routes to specialists ONLY for technical issues or billing problems
  - Always asks about customer status (new vs existing) to access ticket history
  - Focuses on lead generation and contact information capture
- **Routes to**: `support` (technical issues) or `billing` (payment/cancellation)

### 2. **Guardrails** (Security Layer)
- **Input Validation**: Prompt-based security checking before processing
- **Output Sanitization**: Removes leaked system prompts or sensitive data
- **Blocks**: Prompt injection, out-of-scope requests, inappropriate content
- **Context-Aware**: Maintains customer name for personalized redirects

### 3. **Specialist Agents**
- **Sales Agent**: Lead capture, service inquiries, upselling
- **Support Agent**: Technical troubleshooting, router issues, speed problems
- **Billing Agent**: Payment issues, cancellations, account management

### 4. **Tools**
- **Zendesk Tools**: Create tickets, retrieve customer history, filter sales tickets
- **TeleCorp Tools**: Access knowledge base (pricing, FAQs, guides, company info)
- **Utilities**: Validation, formatting, ticket filtering helpers

### 5. **Knowledge Base**
Located at `telecorpBaseKnowledge/`:
- Plans and pricing PDFs
- Technical guides (speed testing, router configuration)
- Company information
- FAQs

## Conversation Flow

```
User Input
    ↓
[Input Validation] ← Guardrail checks for security threats
    ↓
[Supervisor Agent] ← Sales-focused, identifies if specialist needed
    ↓
    ├─→ [Sales Agent] (default handling)
    ├─→ [Support Agent] (technical issues only)
    └─→ [Billing Agent] (billing issues only)
    ↓
[Output Sanitization] ← Remove sensitive info
    ↓
User Response
```

## Key Features

### Sales-First Approach
- Every conversation is a potential sales opportunity
- Supervisor handles general inquiries and lead generation
- Specialists are invoked only when necessary

### Customer Identification
- Always asks: "Are you an existing customer or new?"
- Existing customers: Retrieves ticket history via email
- New customers: Focuses on lead capture and qualification

### Smart Ticket Filtering
- Sales/lead tickets are hidden from customer ticket lists (internal only)
- Customers see only support and billing tickets

### Security
- Prompt-based validation (not rigid word matching)
- Handles prompt injection, jailbreak attempts, DAN attacks
- Context-aware responses when blocking requests

## Configuration

Key settings in `config/langgraph_config.py`:
```python
OPENAI_API_KEY: str          # From environment
DEFAULT_MODEL: str           # gpt-3.5-turbo
COMPANY_NAME: str            # TeleCorp
SUPPORT_PHONE: str           # 1-800-TELECORP
ENABLE_GUARDRAILS: bool      # True
RECURSION_LIMIT: int         # 50
```

## Models Used

- **Supervisor (Router)**: GPT-4 (better for sales conversations and routing)
- **Agents**: GPT-4 (support, sales, billing)
- **Guardrails**: GPT-3.5-turbo (fast, efficient validation)

## State Management

The `ConversationState` tracks:
- `messages`: Conversation history (LangGraph managed)
- `current_persona`: Current active agent
- `route_to`: Target agent for routing
- `is_existing_client`: Customer status (new/existing)
- `customer_email`: For ticket lookup
- `existing_tickets`: Customer ticket history
- `security_blocked`: Guardrail flag
- `threat_type`: Type of security threat detected

## Tools Available to Agents

### Zendesk Tools
- `create_support_ticket()` - Technical/billing support tickets
- `create_sales_ticket()` - Sales leads with contact info
- `get_user_tickets()` - Retrieve customer ticket history
- `get_ticket_details()` - Detailed ticket information

### TeleCorp Tools
- `get_telecorp_plans_pricing()` - Plans and pricing info
- `get_telecorp_company_info()` - Company background
- `get_telecorp_faq()` - Frequently asked questions
- `get_internet_speed_guide()` - Speed troubleshooting
- `get_router_configuration_guide()` - Router setup help
- `get_technical_troubleshooting_steps()` - Step-by-step guides

## Recent Improvements

1. **Removed ~745 lines** of unused code (comments, configs, old implementations)
2. **Refactored tools** - Separated utilities from tool functions
3. **Simplified routing** - Sales-first with selective specialist routing
4. **Context-aware guardrails** - Personalized blocking messages
5. **Clean architecture** - Clear separation of concerns

## Dependencies

- **LangChain**: Agent framework and document processing
- **LangGraph**: Multi-agent orchestration and state management
- **OpenAI**: GPT models for agents and validation
- **Zendesk SDK**: Ticket creation and management

## Usage Example

```python
from src.integrations.zendesk.langgraph_agent.graphs.telecorp_graph import telecorp_graph

# Initialize conversation
config = {"configurable": {"thread_id": "session_123"}}

# Send user message
result = await telecorp_graph.ainvoke(
    {"messages": [HumanMessage(content="Hi, I need help with my internet")]},
    config=config
)

# Get AI response
ai_response = result["messages"][-1].content
```

## Testing

Run the chat frontend:
```bash
python3 chat_frontend.py
```

## Notes

- The system prioritizes lead generation over pure customer service
- Guardrails use modern prompt-based validation (not rigid word matching)
- All ticket templates are centralized in `tools/templates/`
- Knowledge base files must be in `telecorpBaseKnowledge/` directory