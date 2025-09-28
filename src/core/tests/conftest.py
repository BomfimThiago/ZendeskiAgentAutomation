"""
Test fixtures and configuration for core module tests.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Dict, Any
import httpx

from src.core.http_client import AsyncHTTPClientConfig, APIError


@pytest.fixture
def mock_config():
    """Mock AsyncHTTPClientConfig."""
    config = Mock(spec=AsyncHTTPClientConfig)
    config.REQUEST_TIMEOUT = 30
    config.MAX_RETRIES = 3
    config.BACKOFF_FACTOR = 1.0
    config.RATE_LIMIT_RETRY_AFTER = 60
    return config


@pytest.fixture
def sample_headers():
    """Sample HTTP headers."""
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token",
        "User-Agent": "test-client/1.0"
    }


@pytest.fixture
def base_url():
    """Sample base URL."""
    return "https://api.example.com"


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.request = AsyncMock()
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def success_response():
    """Sample successful API response."""
    return {"status": "success", "data": {"id": 123, "name": "test"}}


@pytest.fixture
def error_response():
    """Sample error API response."""
    return {"error": "Bad Request", "message": "Invalid parameters"}


@pytest.fixture
def mock_httpx_response():
    """Mock httpx Response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.headers = {}
    response.content = b'{"status": "success"}'
    response.json.return_value = {"status": "success"}
    return response


@pytest.fixture
def mock_error_response():
    """Mock httpx error Response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 400
    response.headers = {}
    response.content = b'{"error": "Bad Request"}'
    response.json.return_value = {"error": "Bad Request"}
    return response


@pytest.fixture
def mock_rate_limit_response():
    """Mock httpx rate limit Response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 429
    response.headers = {"Retry-After": "30"}
    response.content = b'{"error": "Rate Limited"}'
    response.json.return_value = {"error": "Rate Limited"}
    return response