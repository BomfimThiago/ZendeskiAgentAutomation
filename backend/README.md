# TeleCorp Backend API

FastAPI-based backend for the TeleCorp AI Assistant application with LangGraph multi-agent system.

## Features

- 🤖 Multi-agent LangGraph system (Sales, Support, Billing agents)
- 🎯 Intelligent conversation routing
- 🛡️ Security guardrails for prompt injection protection
- 🎫 Zendesk integration for ticket management
- 📊 LangSmith tracing support
- 🔄 Session-based conversation memory
- 📝 Comprehensive logging and error handling

## Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Zendesk account with API credentials (optional)

## Installation

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements/base.txt
# For development
pip install -r requirements/dev.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Freshdesk Configuration (if using Freshdesk)
FRESHDESK_DOMAIN=your-domain.freshdesk.com
FRESHDESK_API_KEY=your-api-key

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your-openai-api-key

# LangSmith (Optional - for tracing)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=TelecorpAIAutomation
```

## Running the Server

### Development Mode

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
- `GET /health` - Server health status

### Chat API
- `POST /api/v1/ai/chat` - Send message to AI assistant
- `GET /api/v1/ai/chat/hello` - Get welcome message

### Zendesk API
- `GET /api/v1/zendesk/tickets` - List tickets
- `GET /api/v1/zendesk/tickets/{id}` - Get ticket by ID
- `GET /api/v1/zendesk/tickets/search/by-email` - Search tickets by email

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /api/v1/openapi.json` - OpenAPI specification

## Project Structure

```
backend/
├── src/
│   ├── api/                    # API routes
│   │   └── router.py
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Configuration
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── http_client.py     # HTTP client
│   │   └── logging_config.py  # Logging setup
│   ├── integrations/
│   │   └── zendesk/           # Zendesk integration
│   │       ├── langgraph_agent/  # LangGraph multi-agent system
│   │       │   ├── nodes/        # Agent nodes
│   │       │   ├── tools/        # Agent tools
│   │       │   ├── graphs/       # Graph definitions
│   │       │   └── state/        # State management
│   │       ├── chat_router.py    # Chat API endpoints
│   │       ├── chat_schemas.py   # Chat Pydantic models
│   │       └── client.py         # Zendesk API client
│   └── main.py                # FastAPI application
├── telecorpBaseKnowledge/     # Knowledge base documents
├── requirements/              # Python dependencies
├── logs/                      # Application logs
├── .env                       # Environment variables
└── pytest.ini                 # Test configuration
```

## Testing

```bash
cd backend
pytest
```

## LangGraph Agent System

The backend uses a multi-agent system with:

- **Conversation Router** (Supervisor) - Sales-focused default agent
- **Sales Agent** - Lead generation and service inquiries
- **Support Agent** - Technical troubleshooting
- **Billing Agent** - Payment and account management
- **Guardrails** - Security validation layer

## Knowledge Base

Place your knowledge base documents in `telecorpBaseKnowledge/`:
- Plans and pricing PDFs
- Technical guides
- FAQs
- Company information

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| FRESHDESK_DOMAIN | No | Freshdesk domain |
| FRESHDESK_API_KEY | No | Freshdesk API key |
| OPENAI_API_KEY | Yes | OpenAI API key |
| LANGSMITH_TRACING | No | Enable LangSmith tracing |
| LANGSMITH_API_KEY | No | LangSmith API key |
| LANGSMITH_PROJECT | No | LangSmith project name |

## Logging

Logs are stored in the `logs/` directory with the following levels:
- ERROR - Critical errors
- WARNING - Warning messages
- INFO - General information
- DEBUG - Detailed debugging information

Configure logging in `logging.ini`.
