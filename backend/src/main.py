from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from src.core.config import settings
from src.api.router import api_router
from src.core.exceptions import DetailedHTTPException
from src.core.error_handlers import (
    detailed_http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from src.core.logging_config import setup_logging, get_logger
from src.core.middleware import LoggingMiddleware, RequestContextMiddleware

setup_logging()
logger = get_logger("main")


def create_application() -> FastAPI:
    logger.info("Creating FastAPI application")

    app_configs = {
        "title": "Zendesk Agent Automation API",
        "description": "Smart Ticket Tagger and automation system for Zendesk",
        "version": "1.0.0",
        "openapi_url": "/api/v1/openapi.json",
    }

    application = FastAPI(**app_configs)

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(LoggingMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix="/api")

    application.add_exception_handler(DetailedHTTPException, detailed_http_exception_handler)
    application.add_exception_handler(ValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, general_exception_handler)

    logger.info("FastAPI application created successfully")
    return application


app = create_application()


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy"}