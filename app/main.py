"""
Main FastAPI application for AI Startup Copilot.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.api.v1.endpoints import router as api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("🚀 Starting up AI Startup Copilot API Phase 2...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"Celery Broker: {settings.CELERY_BROKER_URL}")
    logger.info(f"MongoDB URI: {settings.MONGO_URI}")
    logger.info(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    logger.info(f"LLM Model: {settings.OLLAMA_MODEL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    
    # Test Redis connection
    try:
        import redis
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed: {e}")
    
    # Test MongoDB connection and create indexes
    try:
        from app.core.mongo_client import get_async_mongo_client, create_indexes
        
        # Test connection
        client = await get_async_mongo_client()
        await client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
        
        # Create database indexes
        await create_indexes()
        logger.info("✅ MongoDB indexes created")
        
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed: {e}")
    
    # Test Ollama connection (optional, don't fail startup if not available)
    try:
        from app.core.embeddings import test_embeddings_connection
        embeddings_test = await test_embeddings_connection()
        if embeddings_test.get("status") == "healthy":
            logger.info("✅ Ollama embeddings service available")
        else:
            logger.warning(f"⚠️  Ollama embeddings service unavailable: {embeddings_test.get('error', 'Unknown error')}")
    except Exception as e:
        logger.warning(f"⚠️  Ollama embeddings test failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🔒 Shutting down AI Startup Copilot API...")
    
    # Close MongoDB connections
    try:
        from app.core.mongo_client import close_async_mongo_client
        await close_async_mongo_client()
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )


# Include API routers
app.include_router(
    api_v1_router,
    prefix=settings.API_V1_STR,
    tags=["api_v1"]
)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Welcome to AI Startup Copilot API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


# Additional health endpoint at root level
@app.get("/health", tags=["health"])
async def health():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
