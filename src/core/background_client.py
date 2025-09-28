"""
Background task client for FastAPI applications.

This module provides a robust client for managing background tasks with
automatic retry mechanisms, error handling, and structured logging. It wraps
FastAPI's BackgroundTasks to provide additional reliability and observability
for asynchronous operations.
"""
import asyncio
import logging
from typing import Any, Callable, Dict, Optional
from functools import wraps

from fastapi import BackgroundTasks

from src.core.logging_config import get_logger, log_with_context

logger = get_logger("background_client")


class BackgroundTaskClient:
    """Client for managing background tasks with error handling and retry mechanisms."""

    def __init__(self):
        self.background_tasks: Optional[BackgroundTasks] = None

    def set_background_tasks(self, background_tasks: BackgroundTasks) -> None:
        """Set the FastAPI BackgroundTasks instance for this request."""
        self.background_tasks = background_tasks

    def add_task(
        self,
        func: Callable,
        *args,
        task_name: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> None:
        """
        Add a background task with error handling and retry mechanisms.

        Args:
            func: Function to be executed
            *args: Function arguments
            task_name: Task name for logging
            max_retries: Maximum number of retry attempts
            **kwargs: Function keyword arguments
        """
        if not self.background_tasks:
            raise RuntimeError("BackgroundTasks not configured. Use set_background_tasks()")

        task_name = task_name or func.__name__

        wrapped_func = self._create_task_wrapper(func, task_name, max_retries)

        self.background_tasks.add_task(wrapped_func, *args, **kwargs)

        log_with_context(
            logger,
            logging.INFO,
            f"Background task '{task_name}' added",
            task_name=task_name,
            max_retries=max_retries,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )

    def _create_task_wrapper(self, func: Callable, task_name: str, max_retries: int) -> Callable:
        """Create wrapper for function with error handling and retry."""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            last_error = None

            while attempt <= max_retries:
                try:
                    log_with_context(
                        logger,
                        logging.INFO,
                        f"Executing task '{task_name}' - attempt {attempt}",
                        task_name=task_name,
                        attempt=attempt,
                        max_retries=max_retries
                    )

                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    log_with_context(
                        logger,
                        logging.INFO,
                        f"Task '{task_name}' executed successfully",
                        task_name=task_name,
                        attempt=attempt
                    )

                    return result

                except Exception as e:
                    last_error = e

                    log_with_context(
                        logger,
                        logging.WARNING,
                        f"Task '{task_name}' failed on attempt {attempt}",
                        task_name=task_name,
                        attempt=attempt,
                        max_retries=max_retries,
                        error=str(e),
                        error_type=type(e).__name__
                    )

                    if attempt == max_retries:
                        log_with_context(
                            logger,
                            logging.ERROR,
                            f"Task '{task_name}' failed permanently after {max_retries} attempts",
                            task_name=task_name,
                            max_retries=max_retries,
                            final_error=str(last_error),
                            error_type=type(last_error).__name__
                        )
                        break

                    attempt += 1
                    wait_time = 2 ** (attempt - 1)
                    await asyncio.sleep(wait_time)

            return None

        return wrapper


background_client = BackgroundTaskClient()


def get_background_client() -> BackgroundTaskClient:
    """Dependency to get the background tasks client."""
    return background_client

