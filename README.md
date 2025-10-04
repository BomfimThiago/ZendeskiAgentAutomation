# TeleCorp AI Assistant - Monorepo

A complete customer support solution with multi-agent AI system built using LangGraph, FastAPI backend, and React frontend.

## 🏗️ Project Structure

```
TeleCorp/
├── backend/           # FastAPI backend with LangGraph agents
├── frontend/          # React TypeScript frontend
├── .env              # Root environment configuration
├── .env.example      # Example environment variables
└── README.md         # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** for backend
- **Node.js 14+** for frontend
- **OpenAI API key** (required)
- **Freshdesk/Zendesk credentials** (optional)

### 1. Clone Repository

```bash
git clone <repository-url>
cd ZendeskiAgentAutomation
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run backend server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env if needed (default points to localhost:8000)

# Run frontend
npm start
```

Frontend will open at: `http://localhost:3000`

## 📚 Documentation

- **Backend Documentation**: See [backend/README.md](backend/README.md)
- **Frontend Documentation**: See [frontend/README.md](frontend/README.md)

## 🎯 Features

### Backend
- 🤖 **Multi-Agent System**: Sales, Support, and Billing specialized agents
- 🎯 **Intelligent Routing**: LangGraph-powered conversation management
- 🛡️ **Security Guardrails**: Prompt injection and jailbreak protection
- 🎫 **Ticket Management**: Zendesk/Freshdesk integration
- 📊 **Tracing**: LangSmith support for debugging
- 🔄 **Session Memory**: Persistent conversation context

### Frontend
- 💬 **Real-time Chat**: Interactive chat interface
- 📱 **Responsive Design**: Works on mobile and desktop
- ⚡ **TypeScript**: Full type safety
- 🎨 **Modern UI**: Gradient design with smooth animations
- ✅ **Status Indicators**: Connection and typing status
- ⌨️ **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line

## 🔧 Configuration

### Backend Environment Variables

```bash
# Freshdesk (Optional)
FRESHDESK_DOMAIN=your-domain.freshdesk.com
FRESHDESK_API_KEY=your-api-key

# OpenAI (Required)
OPENAI_API_KEY=your-openai-api-key

# LangSmith (Optional - for tracing)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=TelecorpAIAutomation
```

### Frontend Environment Variables

```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## 📡 API Endpoints

### Chat
- `POST /api/v1/ai/chat` - Send message to AI assistant
- `GET /api/v1/ai/chat/hello` - Get welcome message

### Tickets (Zendesk/Freshdesk)
- `GET /api/v1/zendesk/tickets` - List tickets
- `GET /api/v1/zendesk/tickets/{id}` - Get ticket details
- `GET /api/v1/zendesk/tickets/search/by-email` - Search by email

### Utilities
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🏗️ Architecture

### Backend Architecture

```
LangGraph Multi-Agent System
├── Conversation Router (Supervisor)
│   ├── Sales Agent (Lead generation)
│   ├── Support Agent (Technical issues)
│   └── Billing Agent (Payments)
├── Guardrails (Security layer)
├── Knowledge Base Tools
└── Ticket Management Tools
```

### Conversation Flow

```
User Message → Input Validation → Supervisor Agent
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              Sales Agent      Support Agent     Billing Agent
                    └─────────────────┬─────────────────┘
                                      ↓
                         Output Sanitization → Response
```

## 🛡️ Security Features

- ✅ Prompt injection protection
- ✅ Jailbreak attempt blocking
- ✅ Out-of-scope request handling
- ✅ Output sanitization
- ✅ Context-aware security

## 📦 Technologies

### Backend
- FastAPI - Modern Python web framework
- LangGraph - Multi-agent orchestration
- LangChain - Agent framework
- OpenAI GPT-4 - Language models
- Pydantic - Data validation
- SQLAlchemy - Database ORM (if needed)

### Frontend
- React 18 - UI framework
- TypeScript - Type safety
- CSS3 - Styling with animations
- Fetch API - HTTP requests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📝 License

[Your License Here]

## 🔗 Links

- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **LangSmith**: https://smith.langchain.com/
- **OpenAI**: https://platform.openai.com/

## 💡 Support

For issues and questions:
- Backend: See [backend/README.md](backend/README.md)
- Frontend: See [frontend/README.md](frontend/README.md)
- Create an issue on GitHub

---

Built with using LangGraph, FastAPI, and React
