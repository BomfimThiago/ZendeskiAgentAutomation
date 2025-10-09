# MyAwesomeFakeCompany Backend API

FastAPI-based backend for the MyAwesomeFakeCompany AI Assistant application with LangGraph multi-agent system.

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
LANGSMITH_PROJECT=MyAwesomeFakeCompany
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
├── myawesomefakecompanyBaseKnowledge/  # Knowledge base documents
├── requirements/              # Python dependencies
├── logs/                      # Application logs
├── .env                       # Environment variables
└── pytest.ini                 # Test configuration
```

## Testing

### Quick Test

```bash
# Run all tests
./run_tests.sh all

# Run with coverage report
./run_tests.sh coverage

# Run specific test suites
./run_tests.sh security      # Security tests only
./run_tests.sh tools         # Tool tests only
./run_tests.sh nodes         # Node tests only
./run_tests.sh critical      # Critical security tests

# Run tests for specific weeks
./run_tests.sh week1         # Week 1: Tools & Security
./run_tests.sh week2         # Week 2: Nodes
```

### Test Suite Details

**196 Total Tests:**
- 189 passing (96.4%)
- 7 deselected (unimplemented pattern detector features)

**Coverage:**
- ✅ Q-LLM intent extraction (17 tests)
- ✅ Dual-LLM security architecture validation
- ✅ Specialized agents (support, sales, billing, quarantined)
- ✅ Graph routing and conversation flows
- ✅ Zendesk integration tools
- ✅ Pattern-based security detection
- ✅ End-to-end integration tests

### Manual Test Execution

```bash
# Using uv (recommended)
uv run pytest tests/ src/ -v

# Using pytest directly
pytest tests/ src/ -v
```

## CI/CD Pipeline

### GitHub Actions Workflow

The project uses GitHub Actions to automatically run tests on every pull request.

**Workflow: `.github/workflows/test.yml`**

**Triggers:**
- Pull requests to `main` or `develop` branches
- Pushes to `main` branch
- Changes in `src/`, `tests/`, or configuration files

**Jobs:**
1. Checkout code
2. Set up Python 3.12
3. Install `uv` package manager
4. Install dependencies
5. Run full test suite (189 tests)
6. Upload coverage artifacts

### Branch Protection

To enforce test requirements on pull requests:

1. **Navigate to:** Repository Settings → Branches → Add rule
2. **Branch pattern:** `main`
3. **Enable:**
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Add required status check: `test`

See `.github/BRANCH_PROTECTION.md` for detailed setup instructions.

### What This Accomplishes

- ✅ **Automated testing** on every PR
- ✅ **Zero failing tests** required to merge
- ✅ **Security validation** through Dual-LLM architecture tests
- ✅ **Code quality** enforcement via required checks

### Testing Before Push

Always run tests locally before creating a PR:

```bash
./run_tests.sh all
```

Expected output:
```
================ 189 passed, 7 deselected, 7 warnings in 3.62s =================
```

## LangGraph Agent System

The backend uses a multi-agent system with:

- **Conversation Router** (Supervisor) - Sales-focused default agent
- **Sales Agent** - Lead generation and service inquiries
- **Support Agent** - Technical troubleshooting
- **Billing Agent** - Payment and account management
- **Guardrails** - Security validation layer

## Knowledge Base

Place your knowledge base documents in `myawesomefakecompanyBaseKnowledge/`:
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
