import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.logging_config import get_logger

logger = get_logger("middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        request_id = str(uuid.uuid4())

        start_time = time.time()

        logger.info(
            "Request started",
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }
            }
        )

        request.state.request_id = request_id

        try:
            response = await call_next(request)

            process_time = time.time() - start_time

            logger.info(
                "Request completed",
                extra={
                    "extra_data": {
                        "request_id": request_id,
                        "method": request.method,
                        "url": str(request.url),
                        "status_code": response.status_code,
                        "process_time": round(process_time, 4),
                    }
                }
            )

            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            process_time = time.time() - start_time

            logger.error(
                "Request failed",
                extra={
                    "extra_data": {
                        "request_id": request_id,
                        "method": request.method,
                        "url": str(request.url),
                        "error": str(exc),
                        "process_time": round(process_time, 4),
                    }
                },
                exc_info=True
            )

            raise exc


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to all log records."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response: 
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        response = await call_next(request)
        return response