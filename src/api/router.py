from fastapi import APIRouter

from src.api.hello import router as hello_router

api_router = APIRouter()

api_router.include_router(hello_router, prefix="/hello", tags=["Hello World"])