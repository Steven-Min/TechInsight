from fastapi import APIRouter

from app.api.v1 import articles

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(articles.router)
