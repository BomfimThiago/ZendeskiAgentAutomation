from fastapi import APIRouter

from src.integrations.zendesk import zendesk_router

api_router = APIRouter()

# Include Zendesk routes
api_router.include_router(
    zendesk_router,
    prefix="/zendesk"
)