"""TeleCorp AI agent node for LLM processing."""

import time
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langsmith import traceable

from ..state.conversation_state import ConversationState
from ..config.langgraph_config import telecorp_config
from ..prompts.persona import TELECORP_PERSONA


@traceable(
    name="telecorp_agent",
    tags=["llm", "customer_support", "telecorp", "openai"],
    metadata={"component": "ai_agent", "version": "1.0", "model": telecorp_config.DEFAULT_MODEL}
)
async def telecorp_agent_node(state: ConversationState) -> Dict[str, Any]:
    """
    Core TeleCorp AI agent processing using LangChain LLM.

    This node handles the main conversation logic, integrating with
    the existing TeleCorp persona and maintaining conversation context.
    """
    start_time = time.time()

    user_input = state.get("user_input", "")
    conversation_history = state.get("conversation_history", [])

    llm = ChatOpenAI(
        openai_api_key=telecorp_config.OPENAI_API_KEY,
        model=telecorp_config.DEFAULT_MODEL,
        temperature=telecorp_config.TEMPERATURE,
        max_tokens=telecorp_config.MAX_TOKENS
    )

    messages = [SystemMessage(content=TELECORP_PERSONA)]

    for msg in conversation_history[-10:]:  # Keep last 10 messages for context
        # Handle both object and dict formats
        role = msg.role if hasattr(msg, 'role') else msg.get('role')
        content = msg.content if hasattr(msg, 'content') else msg.get('content')

        if role == "human":
            messages.append(HumanMessage(content=content))

    messages.append(HumanMessage(content=user_input))

    try:
        response = await llm.ainvoke(messages)
        assistant_response = response.content

        processing_time = time.time() - start_time

        # Add LangSmith metrics
        langsmith_metrics = {
            "llm_processing_duration": processing_time,
            "input_length": len(user_input),
            "output_length": len(assistant_response),
            "message_count": len(messages),
            "model_used": telecorp_config.DEFAULT_MODEL,
            "temperature": telecorp_config.TEMPERATURE,
            "max_tokens": telecorp_config.MAX_TOKENS,
            "telecorp_component": "llm_agent",
            "conversation_history_length": len(conversation_history)
        }

        return {
            "assistant_response": assistant_response,
            "final_response": assistant_response,
            "error_occurred": False,
            "workflow_step": "ai_processed",
            "processing_time": processing_time,
            "metadata": {
                **state.get("metadata", {}),
                "llm_processing_time": processing_time,
                "message_count": len(messages),
                "model_used": telecorp_config.DEFAULT_MODEL,
                "langsmith_metrics": langsmith_metrics
            }
        }

    except Exception as e:
        processing_time = time.time() - start_time
        error_response = telecorp_config.TECHNICAL_DIFFICULTIES_MESSAGE

        return {
            "assistant_response": error_response,
            "final_response": error_response,
            "error_occurred": True,
            "error_message": str(e),
            "workflow_step": "ai_error",
            "processing_time": processing_time,
            "metadata": {
                **state.get("metadata", {}),
                "llm_error_time": processing_time,
                "error_type": type(e).__name__
            }
        }