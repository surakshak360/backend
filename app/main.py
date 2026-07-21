import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.metrics import http_requests_total, http_request_duration_seconds
from app.core.database import (
    connect_to_mongo, close_mongo_connection,
    connect_to_neo4j, close_neo4j_connection,
    connect_to_redis, close_redis_connection
)
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler
)
from app.api.v1.router import api_router
from app.api.openapi import custom_openapi


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting up Surakshak360 Backend API...")
    await connect_to_mongo()
    await connect_to_neo4j()
    await connect_to_redis()
    yield
    logger.info("Shutting down Surakshak360 Backend API...")
    await close_mongo_connection()
    await close_neo4j_connection()
    await close_redis_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:8]}")
    request.state.request_id = request_id
    
    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    response.headers["X-Request-ID"] = request_id

    # Prometheus metrics (skip /metrics itself to avoid recursion)
    path = request.url.path
    if not path.endswith("/metrics"):
        http_requests_total.labels(
            method=request.method,
            path=path,
            status=response.status_code,
        ).inc()
        http_request_duration_seconds.labels(
            method=request.method, path=path
        ).observe((time.time() - start_time))

    logger.info(
        "http_request",
        method=request.method,
        path=path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2),
        request_id=request_id
    )
    return response

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def root_health():
    return {"status": "healthy", "service": "backend", "version": settings.VERSION}


@app.get("/metrics", tags=["Health"], include_in_schema=False)
async def prometheus_metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from app.core.metrics import registry
    return PlainTextResponse(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }

# Attach custom OpenAPI
app.openapi = lambda: custom_openapi(app)
