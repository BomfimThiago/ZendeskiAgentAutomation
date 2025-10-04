"""
Simple logging configuration for development.

This module provides basic logging setup with structured logging support
and extra context data capabilities.
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any


def setup_logging() -> None:
    """Setup simple logging configuration for development."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    configure_logging()


def configure_logging() -> None:
    """Configure simple logging setup."""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }
    logging.config.dictConfig(logging_config)




def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the app prefix."""
    return logging.getLogger(f"app.{name}")


class LoggerMixin:
    """Mixin to add logging capability to any class."""

    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any
) -> None:
    """Log a message with additional context."""
    if context:
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        message = f"{message} | {context_str}"
    logger.log(level, message)