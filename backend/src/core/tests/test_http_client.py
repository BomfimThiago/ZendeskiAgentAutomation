"""
Unit tests for AsyncHTTPClient.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, Mock
import httpx
import asyncio

from src.core.http_client import AsyncHTTPClient, APIError, AsyncHTTPClientConfig


class TestAsyncHTTPClient:
    """Test AsyncHTTPClient functionality."""

    def test_client_initialization(self, base_url, sample_headers, mock_config):
        """Test client initializes with correct parameters."""
        client = AsyncHTTPClient(base_url, sample_headers, mock_config)

        assert client.base_url == base_url
        assert client.headers == sample_headers
        assert client.config == mock_config
        assert client._client is None

    @pytest.mark.asyncio
    async def test_client_connect(self, base_url, sample_headers, mock_config):
        """Test client connection setup."""
        with patch('src.core.http_client.httpx.AsyncClient') as mock_httpx_client_class:
            mock_httpx_client = AsyncMock()
            mock_httpx_client_class.return_value = mock_httpx_client

            client = AsyncHTTPClient(base_url, sample_headers, mock_config)
            await client.connect()

            mock_httpx_client_class.assert_called_once_with(
                base_url=base_url,
                headers=sample_headers,
                timeout=mock_config.REQUEST_TIMEOUT
            )
            assert client._client == mock_httpx_client

    @pytest.mark.asyncio
    async def test_client_disconnect(self, base_url, sample_headers, mock_config):
        """Test client disconnection."""
        mock_httpx_client = AsyncMock()

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        await client.disconnect()
        mock_httpx_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self, base_url, sample_headers, mock_config):
        """Test async context manager functionality."""
        with patch('src.core.http_client.httpx.AsyncClient') as mock_httpx_client_class:
            mock_httpx_client = AsyncMock()
            mock_httpx_client_class.return_value = mock_httpx_client
            
            async with AsyncHTTPClient(base_url, sample_headers, mock_config) as client:
                assert client._client is not None
            # Client should be disconnected after context exit
            mock_httpx_client.aclose.assert_called_once()

    def test_client_property_not_connected(self, base_url, sample_headers, mock_config):
        """Test client property raises error when not connected."""
        client = AsyncHTTPClient(base_url, sample_headers, mock_config)

        with pytest.raises(RuntimeError, match="HTTP client not connected"):
            _ = client.client

    def test_client_property_connected(self, base_url, sample_headers, mock_config):
        """Test client property returns client when connected."""
        mock_httpx_client = AsyncMock()
        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        assert client.client == mock_httpx_client

    @pytest.mark.asyncio
    async def test_make_request_success(self, base_url, sample_headers, mock_config, success_response):
        """Test successful HTTP request."""
        mock_httpx_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = success_response
        mock_httpx_client.request.return_value = mock_response

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        result = await client.make_request("GET", "test/endpoint")

        assert result == success_response
        mock_httpx_client.request.assert_called_once_with(
            method="GET",
            url="/test/endpoint",
            json=None,
            params=None
        )

    @pytest.mark.asyncio
    async def test_make_request_with_data_and_params(self, base_url, sample_headers, mock_config, success_response):
        """Test HTTP request with data and params."""
        mock_httpx_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = success_response
        mock_httpx_client.request.return_value = mock_response

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        test_data = {"key": "value"}
        test_params = {"param": "test"}

        result = await client.make_request("POST", "test/endpoint", data=test_data, params=test_params)

        assert result == success_response
        mock_httpx_client.request.assert_called_once_with(
            method="POST",
            url="/test/endpoint",
            json=test_data,
            params=test_params
        )

    @pytest.mark.asyncio
    async def test_make_request_http_error(self, base_url, sample_headers, mock_config, error_response):
        """Test HTTP request with 4xx/5xx error."""
        mock_httpx_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": "Bad Request"}'
        mock_response.json.return_value = error_response
        mock_httpx_client.request.return_value = mock_response

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        with pytest.raises(APIError) as exc_info:
            await client.make_request("GET", "test/endpoint")

        assert exc_info.value.status_code == 400
        assert exc_info.value.response_data == error_response
        assert "Bad Request" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_custom_error_class(self, base_url, sample_headers, mock_config):
        """Test HTTP request with custom error class."""
        class CustomError(Exception):
            def __init__(self, message, status_code=None, response_data=None):
                self.message = message
                self.status_code = status_code
                self.response_data = response_data
                super().__init__(message)

        mock_httpx_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = b'{"error": "Not Found"}'
        mock_response.json.return_value = {"error": "Not Found"}
        mock_httpx_client.request.return_value = mock_response

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        with pytest.raises(CustomError) as exc_info:
            await client.make_request("GET", "test/endpoint", custom_error_class=CustomError)

        assert isinstance(exc_info.value, CustomError)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_retry(self, base_url, sample_headers, mock_config, success_response):
        """Test rate limit handling with retry."""
        mock_httpx_client = AsyncMock()

        # First response: rate limited
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {"Retry-After": "1"}  # Short wait for testing

        # Second response: success
        success_mock_response = Mock()
        success_mock_response.status_code = 200
        success_mock_response.json.return_value = success_response

        mock_httpx_client.request.side_effect = [rate_limit_response, success_mock_response]

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        with patch('asyncio.sleep') as mock_sleep:
            result = await client.make_request("GET", "test/endpoint")

        assert result == success_response
        assert mock_httpx_client.request.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_default_retry_after(self, base_url, sample_headers, mock_config, success_response):
        """Test rate limit handling with default retry-after."""
        mock_httpx_client = AsyncMock()

        # First response: rate limited without Retry-After header
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {}

        # Second response: success
        success_mock_response = Mock()
        success_mock_response.status_code = 200
        success_mock_response.json.return_value = success_response

        mock_httpx_client.request.side_effect = [rate_limit_response, success_mock_response]

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        with patch('asyncio.sleep') as mock_sleep:
            result = await client.make_request("GET", "test/endpoint")

        assert result == success_response
        mock_sleep.assert_called_once_with(mock_config.RATE_LIMIT_RETRY_AFTER)

    @pytest.mark.asyncio
    async def test_make_request_network_error_retry(self, base_url, sample_headers, mock_config, success_response):
        """Test network error handling with retry."""
        mock_httpx_client = AsyncMock()

        # First two attempts: network error
        network_error = httpx.RequestError("Connection failed")

        # Third attempt: success
        success_mock_response = Mock()
        success_mock_response.status_code = 200
        success_mock_response.json.return_value = success_response

        mock_httpx_client.request.side_effect = [
            network_error,
            network_error,
            success_mock_response
        ]

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        with patch('asyncio.sleep') as mock_sleep:
            result = await client.make_request("GET", "test/endpoint")

        assert result == success_response
        assert mock_httpx_client.request.call_count == 3
        # Should sleep with backoff: 1.0 * 1, then 1.0 * 2
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self, base_url, sample_headers, mock_config):
        """Test max retries exceeded."""
        mock_httpx_client = AsyncMock()
        network_error = httpx.RequestError("Connection failed")
        mock_httpx_client.request.side_effect = network_error

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        with patch('asyncio.sleep'):
            with pytest.raises(APIError, match="Request failed after 3 attempts"):
                await client.make_request("GET", "test/endpoint")

        assert mock_httpx_client.request.call_count == mock_config.MAX_RETRIES

    @pytest.mark.asyncio
    async def test_make_request_url_formatting(self, base_url, sample_headers, mock_config, success_response):
        """Test URL formatting for different endpoint formats."""
        mock_httpx_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = success_response
        mock_httpx_client.request.return_value = mock_response

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        # Test different endpoint formats
        test_cases = [
            ("endpoint", "/endpoint"),
            ("/endpoint", "/endpoint"),
            ("path/to/endpoint", "/path/to/endpoint"),
            ("/path/to/endpoint", "/path/to/endpoint")
        ]

        for input_endpoint, expected_url in test_cases:
            mock_httpx_client.request.reset_mock()
            await client.make_request("GET", input_endpoint)

            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["url"] == expected_url

    @pytest.mark.asyncio
    async def test_make_request_empty_response_body(self, base_url, sample_headers, mock_config):
        """Test handling of HTTP error with empty response body."""
        mock_httpx_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b''  # Empty response
        mock_response.json.return_value = {}
        mock_httpx_client.request.return_value = mock_response

        client = AsyncHTTPClient(base_url, sample_headers, mock_config)
        client._client = mock_httpx_client

        with pytest.raises(APIError) as exc_info:
            await client.make_request("GET", "test/endpoint")

        assert exc_info.value.status_code == 500
        assert "Unknown error" in str(exc_info.value)


class TestAPIError:
    """Test APIError exception class."""

    def test_api_error_initialization(self):
        """Test APIError initialization."""
        error = APIError("Test error", status_code=400, response_data={"error": "test"})

        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.response_data == {"error": "test"}

    def test_api_error_str_with_status_code(self):
        """Test APIError string representation with status code."""
        error = APIError("Test error", status_code=400)
        assert str(error) == "[400] Test error"

    def test_api_error_str_without_status_code(self):
        """Test APIError string representation without status code."""
        error = APIError("Test error")
        assert str(error) == "Test error"

    def test_api_error_inheritance(self):
        """Test APIError inherits from Exception."""
        error = APIError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"