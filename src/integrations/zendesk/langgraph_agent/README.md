# TeleCorp LangGraph Agent Architecture

## Folder Structure

```
langgraph_agent/
├── graphs/              # Main workflow definitions
│   ├── __init__.py
│   ├── telecorp_graph.py       # Main customer support graph
│   └── testing_graph.py        # Simplified graph for testing
├── nodes/               # Individual processing nodes
│   ├── __init__.py
│   ├── security_guard.py       # Input validation & guardrails
│   ├── context_router.py       # Route between Zendesk/direct chat
│   ├── ticket_lookup.py        # Zendesk ticket retrieval
│   ├── memory_manager.py       # Session/conversation management
│   ├── telecorp_agent.py       # Core LLM processing
│   ├── response_filter.py      # Output validation
│   └── zendesk_updater.py      # Ticket updates & comments
├── state/               # State management & schemas
│   ├── __init__.py
│   ├── conversation_state.py   # Main state definition
│   └── schemas.py              # Pydantic models
├── tools/               # External API integrations
│   ├── __init__.py
│   ├── zendesk_client.py      # Zendesk API wrapper
│   └── knowledge_search.py     # TeleCorp knowledge base
├── memory/              # Conversation persistence
│   ├── __init__.py
│   ├── thread_memory.py       # Short-term thread memory
│   └── persistent_memory.py    # Long-term user/ticket memory
├── guardrails/          # Security & validation
│   ├── __init__.py
│   ├── input_validator.py     # Pre-processing security
│   └── output_validator.py     # Post-processing validation
└── config/              # Configuration & settings
    ├── __init__.py
    └── langgraph_config.py    # LangGraph-specific config
```

## Key Differences from Current Approach

1. **Stateful Workflow**: LangGraph manages conversation state through the entire workflow
2. **Conditional Routing**: Automatic routing between Zendesk ticket context vs. direct chat
3. **Tool Integration**: Native Zendesk API integration as LangGraph tools
4. **Memory Persistence**: Both thread-scoped and cross-session memory management
5. **Enhanced Security**: Guardrails integrated into graph state transitions