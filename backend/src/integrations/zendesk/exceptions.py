"""
Zendesk-specific exceptions.

This module defines custom exceptions for Zendesk API operations,
providing detailed error context for better debugging and handling.
"""
from typing import Dict, Optional


class ZendeskAPIError(Exception):
    """Custom exception for Zendesk API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation with additional context."""
        base_msg = self.message
        if self.status_code:
            base_msg = f"[{self.status_code}] {base_msg}"
        return base_msg

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"ZendeskAPIError(message='{self.message}', status_code={self.status_code})"

    @property
    def is_rate_limit_error(self) -> bool:
        """Check if this is a rate limiting error."""
        return self.status_code == 429

    @property
    def is_auth_error(self) -> bool:
        """Check if this is an authentication error."""
        return self.status_code in (401, 403)

    @property
    def is_not_found_error(self) -> bool:
        """Check if this is a not found error."""
        return self.status_code == 404

    @property
    def is_client_error(self) -> bool:
        """Check if this is a client error (4xx)."""
        return bool(self.status_code and 400 <= self.status_code < 500)

    @property
    def is_server_error(self) -> bool:
        """Check if this is a server error (5xx)."""
        return bool(self.status_code and 500 <= self.status_code < 600)


class ZendeskConnectionError(ZendeskAPIError):
    """Raised when connection to Zendesk fails."""
    pass


class ZendeskTimeoutError(ZendeskAPIError):
    """Raised when Zendesk API request times out."""
    pass


class ZendeskRateLimitError(ZendeskAPIError):
    """Raised when Zendesk rate limit is exceeded."""
    pass