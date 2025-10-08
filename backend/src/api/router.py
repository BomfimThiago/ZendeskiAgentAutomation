from fastapi import APIRouter

from src.integrations.zendesk import chat_router

api_router = APIRouter(prefix="/v1")

# Include Chat routes
api_router.include_router(
    chat_router,
    prefix="/ai"
)