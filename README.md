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

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

Then edit `.env` and configure the following **required** variables:

```bash
# Zendesk Configuration (REQUIRED)
# Get from: https://your-subdomain.zendesk.com/admin/apps-integrations/apis/zendesk-api
ZENDESK_URL=your-subdomain.zendesk.com
ZENDESK_EMAIL=your-zendesk-email@example.com
ZENDESK_TOKEN=your-zendesk-api-token

# OpenAI Configuration (REQUIRED)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-api-key
```

**Optional configuration** (for advanced features):

```bash
# LangSmith - For debugging and tracing agent behavior (OPTIONAL)
# Sign up at: https://smith.langchain.com/
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=telecorp-agent-automation

# CORS - Custom allowed origins (OPTIONAL, has defaults)
# CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

**Important Notes:**
- `ZENDESK_URL` should be just the subdomain with `.zendesk.com` (e.g., `mycompany.zendesk.com`)
- All **REQUIRED** variables must be set or the application will fail to start
- LangSmith variables are optional and only needed if you want to trace agent executions
- See `.env.example` for the complete list of available configuration options

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

**Option A: Chat Interface (Standalone)**

Run the interactive chat frontend to test the AI agent directly:

```bash
python3 chat_frontend.py
```

**Option B: FastAPI Server (API)**

Run the FastAPI server for API access:

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Access the API:
- API Root: `http://localhost:8000`
- Health Check: `http://localhost:8000/health`
- API Documentation: `http://localhost:8000/docs`
- OpenAPI Spec: `http://localhost:8000/api/v1/openapi.json`

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

## 🚀 Quick Start

Test the AI agent with the interactive chat interface:

```bash
uv run python3 langgraph_chat_frontend.py
```

Or run a quick test to verify functionality:

```bash
uv run python3 test_quick.py
```

## 🛡️ Security Features Verified

The agent successfully blocks inappropriate requests:

- ✅ **Scope violations**: "What's the capital of France?" → Redirects to TeleCorp services
- ✅ **Jailbreak attempts**: "From now on you are DAN..." → Maintains Alex identity
- ✅ **Prompt injection**: "Ignore previous instructions..." → Security protocols maintained
- ✅ **Safe conversations**: "I need help with internet" → Normal TeleCorp support

## 🏗️ Architecture Overview

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

## 🔄 Conversation Flow

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

## 🎯 Core Components

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

## 🧪 Example Conversation

```
🤖 Alex: Hi there! I'm Alex from TeleCorp customer support...

💬 You: What's the capital of France?
🤖 Alex: I'm Alex from TeleCorp customer support, specialized in helping with TeleCorp services. For that type of question, I'd recommend other resources. Do you have any other questions about TeleCorp services?

💬 You: I need help with my internet plan
🤖 Alex: I'd be happy to help you with your internet plan! Can you tell me a bit more about what you're looking for? Are you interested in upgrading your current service, troubleshooting an issue, or exploring our available plans?
```

## ✨ Key Features

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

## 🔧 Configuration

Key settings in `config/langgraph_config.py`:
```python
OPENAI_API_KEY: str          # From environment
DEFAULT_MODEL: str           # gpt-3.5-turbo
COMPANY_NAME: str            # TeleCorp
SUPPORT_PHONE: str           # 1-800-TELECORP
ENABLE_GUARDRAILS: bool      # True
RECURSION_LIMIT: int         # 50
```

## 🤖 Models Used

- **Supervisor (Router)**: GPT-4 (better for sales conversations and routing)
- **Agents**: GPT-4 (support, sales, billing)
- **Guardrails**: GPT-3.5-turbo (fast, efficient validation)

## 🛠️ Tools Available to Agents

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

## 📚 Knowledge Base

The `telecorpBaseKnowledge/` folder contains TeleCorp company information and documentation:
- Plans and pricing PDFs
- Technical guides (speed testing, router configuration)
- Company information
- FAQs

## 📊 State Management

The `ConversationState` tracks:
- `messages`: Conversation history (LangGraph managed)
- `current_persona`: Current active agent
- `route_to`: Target agent for routing
- `is_existing_client`: Customer status (new/existing)
- `customer_email`: For ticket lookup
- `existing_tickets`: Customer ticket history
- `security_blocked`: Guardrail flag
- `threat_type`: Type of security threat detected


## 📦 Dependencies

- **LangChain**: Agent framework and document processing
- **LangGraph**: Multi-agent orchestration and state management
- **OpenAI**: GPT models for agents and validation
- **Zendesk SDK**: Ticket creation and management
