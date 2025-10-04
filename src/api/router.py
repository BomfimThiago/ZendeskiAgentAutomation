from fastapi import APIRouter

from src.integrations.zendesk import zendesk_router, chat_router

api_router = APIRouter(prefix="/v1")

# Include Zendesk routes
api_router.include_router(
    zendesk_router,
    prefix="/zendesk"
)

# Include Chat routes
api_router.include_router(
    chat_router,
    prefix="/ai"
)