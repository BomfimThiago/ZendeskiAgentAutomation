"""
Pydantic schemas for chat API endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message", min_length=1, max_length=5000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: str = Field(..., description="AI assistant response")
    session_id: str = Field(..., description="Session ID for this conversation")
    persona: Optional[str] = Field(None, description="Current active persona/agent")


class ChatHistoryResponse(BaseModel):
    """Response model for chat history."""
    messages: List[ChatMessage] = Field(default_factory=list, description="Conversation history")
    session_id: str = Field(..., description="Session ID")
