# TeleCorp AI Chat Interface

Console frontend to test the TeleCorp AI customer support agent.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements/base.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your-api-key
```

### 3. Run Chat
```bash
python3 chat_frontend.py
```

## How to Test the AI

### Basic Test Questions
```
👤 You: Hello
👤 You: Who are you?
👤 You: What services do you offer?
👤 You: What's your phone number?
```

### Customer Support Tests
```
👤 You: My internet is slow
👤 You: I want to upgrade my plan
👤 You: How do I pay my bill?
👤 You: I need technical support
```

### Memory Test
```
👤 You: I'm having internet issues
👤 You: It started yesterday
👤 You: What did I tell you about my problem?
```

## Commands
- **Chat normally** - Just type your message
- **`quit`** - Exit chat
- **`reset`** - Clear conversation memory

## Troubleshooting

**Missing API Key:**
1. Get key from [OpenAI](https://platform.openai.com/api-keys)
2. Add to `.env`: `OPENAI_API_KEY=sk-your-key`

**Quota Exceeded:**
Add credits at [OpenAI Billing](https://platform.openai.com/account/billing)

## What to Expect

The AI should:
- Introduce itself as "Alex from TeleCorp"
- Know about TeleCorp services
- Remember conversation context
- Provide helpful customer support
- Handle errors gracefully