"""
Generic HTTP client for external API calls.

This module provides a reusable HTTP client with built-in retry logic,
error handling, and rate limiting for all external integrations.
"""
import asyncio
from typing import Dict, Optional, Any, Protocol
import httpx

from .logging_config import get_logger, log_with_context

logger = get_logger("http_client")


class AsyncHTTPClientConfig(Protocol):
    """Protocol for async HTTP client configuration."""
    REQUEST_TIMEOUT: int
    MAX_RETRIES: int
    BACKOFF_FACTOR: float
    RATE_LIMIT_RETRY_AFTER: int


class APIError(Exception):
    """Generic API error for HTTP requests."""

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
        base_msg = self.message
        if self.status_code:
            base_msg = f"[{self.status_code}] {base_msg}"
        return base_msg


class AsyncHTTPClient:
    """Generic async HTTP client with retry logic and error handling."""

    def __init__(self, base_url: str, headers: Dict[str, str], config: AsyncHTTPClientConfig):
        self.base_url = base_url
        self.headers = headers
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Initialize the HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.config.REQUEST_TIMEOUT
        )
        log_with_context(
            logger,
            20,  # INFO
            "HTTP client connected",
            base_url=self.base_url
        )

    async def disconnect(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            log_with_context(logger, 20, "HTTP client disconnected")

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client instance."""
        if not self._client:
            raise RuntimeError("HTTP client not connected. Use 'async with' or call connect()")
        return self._client

    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        custom_error_class: type = APIError
    ) -> Dict[str, Any]:
        """Make an HTTP request with error handling and retries."""
        url = f"/{endpoint.lstrip('/')}"

        for attempt in range(1, self.config.MAX_RETRIES + 1):
            try:
                log_with_context(
                    logger,
                    20,  # INFO
                    f"Making {method} request to {endpoint}",
                    attempt=attempt,
                    url=url
                )

                response = await self.client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.config.RATE_LIMIT_RETRY_AFTER))
                    log_with_context(
                        logger,
                        30,  # WARNING
                        f"Rate limited, waiting {retry_after} seconds",
                        retry_after=retry_after,
                        attempt=attempt
                    )
                    await asyncio.sleep(retry_after)
                    continue

                # Handle other HTTP errors
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    log_with_context(
                        logger,
                        40,  # ERROR
                        f"HTTP error {response.status_code}",
                        status_code=response.status_code,
                        error_data=error_data
                    )
                    raise custom_error_class(
                        f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}",
                        status_code=response.status_code,
                        response_data=error_data
                    )

                # Success
                result = response.json()
                log_with_context(
                    logger,
                    20,  # INFO
                    f"Request successful to {endpoint}",
                    status_code=response.status_code
                )
                return result

            except httpx.RequestError as e:
                log_with_context(
                    logger,
                    40,  # ERROR
                    f"Request error on attempt {attempt}",
                    error=str(e),
                    attempt=attempt
                )
                if attempt == self.config.MAX_RETRIES:
                    raise custom_error_class(f"Request failed after {self.config.MAX_RETRIES} attempts: {e}")

                await asyncio.sleep(self.config.BACKOFF_FACTOR * attempt)

        raise custom_error_class("Max retries exceeded")