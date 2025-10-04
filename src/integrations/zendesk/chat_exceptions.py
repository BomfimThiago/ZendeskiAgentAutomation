"""
Custom API exceptions for chat operations.

This module defines FastAPI-specific exceptions for chat operations,
extending the core DetailedHTTPException to provide proper HTTP status codes.
"""
from fastapi import status
from src.core.exceptions import DetailedHTTPException


class ChatServiceUnavailableException(DetailedHTTPException):
    """Raised when chat service is unavailable."""
    STATUS_CODE = status.HTTP_503_SERVICE_UNAVAILABLE
    DETAIL = "Chat service is currently unavailable"


class ChatGraphNotInitializedException(DetailedHTTPException):
    """Raised when LangGraph graph is not initialized."""
    STATUS_CODE = status.HTTP_503_SERVICE_UNAVAILABLE
    DETAIL = "Chat graph not initialized. Please contact support."


class ChatProcessingException(DetailedHTTPException):
    """Raised when error occurs processing chat message."""
    STATUS_CODE = status.HTTP_500_INTERNAL_SERVER_ERROR
    DETAIL = "Error processing chat message"


class InvalidSessionException(DetailedHTTPException):
    """Raised when session ID is invalid."""
    STATUS_CODE = status.HTTP_400_BAD_REQUEST
    DETAIL = "Invalid session ID"


class MessageTooLongException(DetailedHTTPException):
    """Raised when message exceeds maximum length."""
    STATUS_CODE = status.HTTP_400_BAD_REQUEST
    DETAIL = "Message exceeds maximum length"


class EmptyMessageException(DetailedHTTPException):
    """Raised when message is empty."""
    STATUS_CODE = status.HTTP_400_BAD_REQUEST
    DETAIL = "Message cannot be empty"
