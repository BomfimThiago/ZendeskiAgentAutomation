"""
FastAPI router for chat operations with the TeleCorp AI agent.
"""
import uuid
from fastapi import APIRouter, status
from langchain_core.messages import HumanMessage, AIMessage

from src.core.logging_config import get_logger, log_with_context
from .chat_schemas import ChatRequest, ChatResponse
from .chat_exceptions import (
    ChatServiceUnavailableException,
    ChatGraphNotInitializedException,
    ChatProcessingException
)
from .langgraph_agent.graphs.telecorp_graph import create_telecorp_graph

router = APIRouter(tags=["Chat"])
logger = get_logger("chat_router")

# Initialize the LangGraph graph
telecorp_graph = None
try:
    telecorp_graph = create_telecorp_graph()
    log_with_context(logger, 20, "TeleCorp chat graph initialized successfully")
except Exception as e:
    log_with_context(
        logger,
        40,  # ERROR
        "Failed to initialize TeleCorp graph",
        error=str(e)
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send chat message",
    description="Send a message to the TeleCorp AI assistant and receive a response"
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the AI assistant.

    The assistant maintains conversation history using session_id.
    If no session_id is provided, a new session will be created.
    """
    if not telecorp_graph:
        log_with_context(
            logger,
            40,  # ERROR
            "Chat graph not available"
        )
        raise ChatGraphNotInitializedException()

    # Generate or use existing session ID
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"

    log_with_context(
        logger,
        20,  # INFO
        "Processing chat message",
        session_id=session_id,
        message_length=len(request.message)
    )

    try:
        # Configure with thread ID for memory persistence
        config = {"configurable": {"thread_id": session_id}}

        # Use async invoke since graph nodes are async
        result = await telecorp_graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config
        )

        # Extract the AI response
        ai_response = ""
        current_persona = None

        if result and "messages" in result:
            # Find the last AI message
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    ai_response = msg.content
                    break

            # Get current persona if available
            if "current_persona" in result:
                current_persona = result["current_persona"]

        if not ai_response:
            ai_response = "I apologize, but I'm having trouble responding right now. Please try again."

        log_with_context(
            logger,
            20,  # INFO
            "Chat message processed successfully",
            session_id=session_id,
            persona=current_persona,
            response_length=len(ai_response)
        )

        return ChatResponse(
            message=ai_response,
            session_id=session_id,
            persona=current_persona
        )

    except Exception as e:
        logger.error(
            f"Error processing chat message: {type(e).__name__}: {str(e)}",
            exc_info=True,
            extra={"session_id": session_id}
        )
        raise ChatProcessingException(detail=f"Error processing chat message: {type(e).__name__}: {str(e)}")


@router.get(
    "/chat/hello",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Get welcome message",
    description="Get the initial welcome message from the AI assistant"
)
async def get_welcome_message() -> ChatResponse:
    """
    Get the initial welcome message without starting a conversation.
    """
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    welcome_message = (
        "Hi there! I'm Alex from TeleCorp customer support. "
        "I'm here to help you with any questions about your service or "
        "help you find the right plan for your needs. What can I assist you with today?"
    )

    log_with_context(
        logger,
        20,  # INFO
        "Welcome message generated",
        session_id=session_id
    )

    return ChatResponse(
        message=welcome_message,
        session_id=session_id,
        persona="conversation_router"
    )
