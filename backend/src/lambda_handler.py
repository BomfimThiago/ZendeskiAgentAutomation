"""
AWS Lambda Handler for MyAwesomeFakeCompany Customer Support API

This module wraps the FastAPI application with Mangum adapter to enable
serverless deployment on AWS Lambda + API Gateway.

Usage in Lambda:
    handler = lambda_handler(event, context)

Local testing:
    python -m src.lambda_handler (runs uvicorn)
"""

import os
import sys

# Ensure AWS Lambda can find the src module
if os.environ.get('AWS_EXECUTION_ENV'):
    # Running in Lambda - add /var/task to path
    sys.path.insert(0, '/var/task')

from mangum import Mangum
from src.main import app
from src.core.logging_config import get_logger

logger = get_logger("lambda_handler")

# Mangum adapter - converts API Gateway events to ASGI
handler = Mangum(app, lifespan="off")


def lambda_handler(event, context):
    """
    AWS Lambda handler function.

    Args:
        event: API Gateway event (HTTP request)
        context: Lambda context

    Returns:
        API Gateway response (HTTP response)
    """
    logger.info(
        "Lambda invoked",
        extra={
            "request_id": context.request_id,
            "function_name": context.function_name,
            "http_method": event.get("requestContext", {}).get("http", {}).get("method"),
            "path": event.get("requestContext", {}).get("http", {}).get("path"),
        }
    )

    # Log cold start
    if not hasattr(lambda_handler, "_initialized"):
        logger.info("🥶 COLD START - First invocation")
        lambda_handler._initialized = True

    try:
        response = handler(event, context)
        logger.info(
            "Lambda response generated",
            extra={
                "status_code": response.get("statusCode"),
                "request_id": context.request_id,
            }
        )
        return response
    except Exception as e:
        logger.error(
            f"Lambda handler error: {e}",
            extra={
                "request_id": context.request_id,
                "error_type": type(e).__name__,
            },
            exc_info=True
        )
        # Return 500 error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": '{"error": "Internal server error"}'
        }


# Local development: Run uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    logger.info("Running FastAPI app locally with uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
