# Service Communication Architecture

## **User Makes a Request → Response Flow**

```
┌─────────────┐
│   USER      │ Types message in React frontend
└─────────────┘
       ↓ HTTP POST /api/v1/ai/chat
┌─────────────────────────────────────────────┐
│  API GATEWAY (HTTP API)                     │
│  - Receives HTTPS request                   │
│  - CORS handling                            │
│  - Routes to Lambda                         │
└─────────────────────────────────────────────┘
       ↓ Invokes Lambda (with event payload)
┌─────────────────────────────────────────────┐
│  LAMBDA FUNCTION                            │
│  - FastAPI application                      │
│  - LangGraph multi-agent system             │
│  - Dual-LLM security (Q-LLM + P-LLM)        │
└─────────────────────────────────────────────┘
       ↓
┌──────────────── Lambda Logic ───────────────┐
│                                              │
│  1️⃣ Check Session                           │
│     ↓ Query                                 │
│  ┌─────────────────────┐                    │
│  │ DynamoDB - Sessions │                    │
│  │ Get user context    │                    │
│  └─────────────────────┘                    │
│     ↑ Returns session data                  │
│                                              │
│  2️⃣ Security Check (Q-LLM - Haiku)         │
│     ↓ InvokeModel                           │
│  ┌─────────────────────────┐                │
│  │ BEDROCK - Claude Haiku  │                │
│  │ Fast intent detection   │                │
│  │ "Is this malicious?"    │                │
│  └─────────────────────────┘                │
│     ↑ Returns: safe/malicious               │
│                                              │
│  3️⃣ Check Intent Cache                     │
│     ↓ Query                                 │
│  ┌──────────────────────────┐               │
│  │ DynamoDB - Intent Cache  │               │
│  │ Reuse Q-LLM decision     │               │
│  └──────────────────────────┘               │
│     ↑ Cache hit/miss                        │
│                                              │
│  4️⃣ Process Request (P-LLM - Sonnet)       │
│     ↓ InvokeModel                           │
│  ┌─────────────────────────┐                │
│  │ BEDROCK - Claude Sonnet │                │
│  │ Main agent processing   │                │
│  │ Generate response       │                │
│  └─────────────────────────┘                │
│     ↑ Returns AI response                   │
│                                              │
│  5️⃣ Save Conversation                      │
│     ↓ PutItem                               │
│  ┌─────────────────────────────┐            │
│  │ DynamoDB - Conversations    │            │
│  │ Store message history       │            │
│  └─────────────────────────────┘            │
│                                              │
│  6️⃣ Log Everything                         │
│     ↓ PutLogEvents                          │
│  ┌─────────────────────────┐                │
│  │ CloudWatch Logs         │                │
│  │ Debug & monitoring      │                │
│  └─────────────────────────┘                │
│                                              │
└──────────────────────────────────────────────┘
       ↓ Returns response
┌─────────────────────────────────────────────┐
│  API GATEWAY                                │
│  - Formats response                         │
│  - Adds CORS headers                        │
└─────────────────────────────────────────────┘
       ↓ HTTP 200 + JSON
┌─────────────┐
│   USER      │ Sees AI response in chat
└─────────────┘
```

## **Key Service Communications:**

### **1. API Gateway → Lambda**
- **Trigger**: API Gateway invokes Lambda
- **Auth**: IAM permissions (configured in lambda.tf:142-148)
- **Data**: HTTP request → Lambda event format

### **2. Lambda → Bedrock**
- **Auth**: IAM policy `bedrock:InvokeModel` (iam.tf:43-45)
- **Q-LLM (Haiku)**: Fast security checks (~200ms)
- **P-LLM (Sonnet)**: Main AI processing (~2-3s)

### **3. Lambda → DynamoDB**
- **Auth**: IAM policy `dynamodb:PutItem`, `GetItem`, etc. (iam.tf:72-81)
- **Tables**:
  - `sessions` - User context/state
  - `intent_cache` - Q-LLM decision cache
  - `conversations` - Chat history

### **4. Lambda → CloudWatch**
- **Auth**: IAM policy `logs:PutLogEvents` (iam.tf:113-115)
- **Purpose**: Application logs, errors, debugging

## **Security Flow (Dual-LLM):**

```
User Message
    ↓
Q-LLM (Haiku) - "Is this safe?"
    ├─ Safe → Continue to P-LLM
    └─ Malicious → Block & return error
            ↓
P-LLM (Sonnet) - "Generate response"
    ↓
Response to user
```

## **Data Persistence:**

### **DynamoDB stores**:
- Session state (who the user is, conversation context)
- Intent cache (avoid re-checking same patterns)
- Full conversation history

### **CloudWatch stores**:
- Application logs
- Error traces
- Performance metrics

## **Cost Optimization:**

- **Intent Cache** → Reduces Bedrock calls (saves $$$)
- **DynamoDB On-Demand** → Pay only for actual requests
- **Lambda** → No cost when idle
- **API Gateway HTTP API** → 71% cheaper than REST API

## **IAM Security Model:**

Everything communicates through **IAM permissions** - no passwords, no keys in code. Each service authenticates using the role/policies we created:

1. **Trust Policy** - Lambda can assume the execution role
2. **Bedrock Policy** - Lambda can invoke Claude models
3. **DynamoDB Policy** - Lambda can read/write tables
4. **CloudWatch Policy** - Lambda can write logs
5. **API Gateway Permission** - Can invoke Lambda function

## **Reference Files:**

- IAM Policies: `backend/terraform/iam.tf`
- Lambda Configuration: `backend/terraform/lambda.tf`
- DynamoDB Tables: `backend/terraform/dynamodb.tf`
- API Gateway Setup: `backend/terraform/lambda.tf:66-148`
