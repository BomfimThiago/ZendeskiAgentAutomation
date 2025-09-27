import logging
from fastapi import APIRouter, status

from src.core.models import CustomModel
from src.core.logging_config import get_logger, log_with_context

logger = get_logger("hello")

router = APIRouter()


class HelloResponse(CustomModel):
    message: str
    success: bool = True


@router.get(
    "/",
    response_model=HelloResponse,
    status_code=status.HTTP_200_OK,
    description="Simple hello world endpoint",
    summary="Hello World",
)
async def hello_world() -> HelloResponse:
    logger.info("Hello world endpoint accessed")
    return HelloResponse(message="Hello World from FastAPI!")


@router.get(
    "/greet/{name}",
    response_model=HelloResponse,
    status_code=status.HTTP_200_OK,
    description="Personalized greeting endpoint",
    summary="Personalized Greeting",
)
async def greet_user(name: str) -> HelloResponse:
    log_with_context(
        logger,
        logging.INFO,
        "Greeting user",
        user_name=name,
        name_length=len(name),
    )
    return HelloResponse(message=f"Hello {name}! Welcome to FastAPI!")