from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.core.exceptions import DetailedHTTPException
from src.core.logging_config import get_logger

logger = get_logger("error_handlers")


async def detailed_http_exception_handler(
    request: Request, exc: DetailedHTTPException
) -> JSONResponse:
    """Handle custom HTTP exceptions with detailed error responses."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "extra_data": {
                "request_id": request_id,
                "status_code": exc.status_code,
                "path": str(request.url),
                "method": request.method,
                "exception_type": exc.__class__.__name__,
            }
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
            "request_id": request_id,
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "Validation error",
        extra={
            "extra_data": {
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method,
                "validation_errors": exc.errors(),
            }
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation error",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": str(request.url),
            "request_id": request_id,
            "details": exc.errors(),
        },
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"Unexpected error: {exc}",
        extra={
            "extra_data": {
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method,
                "exception_type": exc.__class__.__name__,
            }
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": str(request.url),
            "request_id": request_id,
        },
    )