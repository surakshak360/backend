from fastapi import APIRouter, Request
from fastapi.openapi.utils import get_openapi
from app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "backend",
        "version": settings.VERSION
    }


@router.get("/schema", tags=["Health"])
async def openapi_schema(request: Request):
    return get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        routes=request.app.routes
    )
