# TeleCorp AI Agent - Zendesk Integration

**LangGraph-powered customer support automation for TeleCorp telecommunications.**

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

This project uses **LangGraph** for building a stateful, multi-step AI agent workflow:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Guard   │───▶│  Context Router  │───▶│  TeleCorp Agent │
│   (Security)    │    │ (Route Decision) │    │   (LLM Core)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │ Response Filter │
                                              │  (Validation)   │
                                              └─────────────────┘
```

## 📁 Project Structure (Consolidated)

```
src/integrations/zendesk/langgraph_agent/    # All TeleCorp agent code
├── graphs/              # Workflow definitions
├── nodes/               # Processing nodes
├── state/               # State management
├── config/              # Configuration
├── prompts/             # TeleCorp persona
├── guardrails/          # Security validation
├── tools/               # Future Zendesk API integration
└── memory/              # Future conversation persistence
```

## 🧪 Example Conversation

```
🤖 Alex: Hi there! I'm Alex from TeleCorp customer support...

💬 You: What's the capital of France?
🤖 Alex: I'm Alex from TeleCorp customer support, specialized in helping with TeleCorp services. For that type of question, I'd recommend other resources. Do you have any other questions about TeleCorp services?

💬 You: I need help with my internet plan
🤖 Alex: I'd be happy to help you with your internet plan! Can you tell me a bit more about what you're looking for? Are you interested in upgrading your current service, troubleshooting an issue, or exploring our available plans?
```

## 🔧 Configuration

Set up your environment variables in `.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 🎯 Key Benefits

1. **Security-First**: Multi-layer protection against attacks and scope violations
2. **Stateful Workflow**: LangGraph manages conversation state through entire process
3. **Modular Design**: Easy to modify individual components without breaking others
4. **Observable**: Clear visibility into each processing step
5. **Scalable**: Ready for Zendesk integration and advanced features

## 👤 TeleCorp Persona

The AI agent operates as **"Alex"** - a professional, helpful TeleCorp customer support specialist with expertise in:
- Internet and broadband services
- Mobile and phone plans
- Billing and account management
- Technical troubleshooting
- Service upgrades and changes