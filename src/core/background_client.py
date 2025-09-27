import asyncio
import logging
from typing import Any, Callable, Dict, Optional
from functools import wraps

from fastapi import BackgroundTasks

from src.core.logging_config import get_logger, log_with_context

logger = get_logger("background_client")


class BackgroundTaskClient:
    def __init__(self):
        self.background_tasks: Optional[BackgroundTasks] = None

    def set_background_tasks(self, background_tasks: BackgroundTasks) -> None:
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

        Args:
            func: Função a ser executada
            *args: Argumentos da função
            task_name: Nome da tarefa para logs
            max_retries: Número máximo de tentativas
            **kwargs: Argumentos nomeados da função
        """
        if not self.background_tasks:
            raise RuntimeError("BackgroundTasks não foi configurado. Use set_background_tasks()")

        task_name = task_name or func.__name__

        wrapped_func = self._create_task_wrapper(func, task_name, max_retries)

        self.background_tasks.add_task(wrapped_func, *args, **kwargs)

        log_with_context(
            logger,
            logging.INFO,
            f"Background task '{task_name}' adicionada",
            task_name=task_name,
            max_retries=max_retries,
            args_count=len(args),
            kwargs_count=len(kwargs)
        )

    def _create_task_wrapper(self, func: Callable, task_name: str, max_retries: int) -> Callable:

        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            last_error = None

            while attempt <= max_retries:
                try:
                    log_with_context(
                        logger,
                        logging.INFO,
                        f"Executando task '{task_name}' - tentativa {attempt}",
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
                        f"Task '{task_name}' executada com sucesso",
                        task_name=task_name,
                        attempt=attempt
                    )

                    return result

                except Exception as e:
                    last_error = e

                    log_with_context(
                        logger,
                        logging.WARNING,
                        f"Task '{task_name}' falhou na tentativa {attempt}",
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
                            f"Task '{task_name}' falhou definitivamente após {max_retries} tentativas",
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
    return background_client


async def send_email_task(to_email: str, subject: str, message: str) -> None:
    log_with_context(
        logger,
        logging.INFO,
        "Enviando email",
        to_email=to_email,
        subject=subject
    )

    await asyncio.sleep(2)

    import random
    if random.random() < 0.3:  # 30% chance de erro
        raise Exception("Falha no servidor de email")

    log_with_context(
        logger,
        logging.INFO,
        "Email enviado com sucesso",
        to_email=to_email
    )


async def process_data_task(data: Dict[str, Any], user_id: int) -> None:
    log_with_context(
        logger,
        logging.INFO,
        "Processando dados",
        user_id=user_id,
        data_size=len(str(data))
    )

    await asyncio.sleep(3)

    log_with_context(
        logger,
        logging.INFO,
        "Dados processados com sucesso",
        user_id=user_id,
        items_processed=len(data) if isinstance(data, dict) else 1
    )


def sync_cleanup_task(file_path: str) -> None:
    import os

    log_with_context(
        logger,
        logging.INFO,
        "Executando limpeza de arquivo",
        file_path=file_path
    )

    import time
    time.sleep(1)

    log_with_context(
        logger,
        logging.INFO,
        "Limpeza concluída",
        file_path=file_path
    )