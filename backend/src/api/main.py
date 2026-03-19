"""
Digital FTE Customer Success Agent - FastAPI Application (Simplified)
Main application entry point for the multi-channel customer support API.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..utils.config import get_settings
from ..utils.logger import get_logger
from ..database.connection import create_pool, close_pool

settings = get_settings()
logger = get_logger(__name__)

__version__ = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager - simplified without Kafka."""

    # Startup
    logger.info(
        "application_starting",
        version=__version__,
        environment=settings.environment,
    )

    try:
        # Initialize database pool
        await create_pool()
        logger.info("database_pool_initialized")
        logger.info("application_ready")
    except Exception as exc:
        logger.error("application_startup_failed", error=str(exc))
        raise

    yield

    # Shutdown
    logger.info("application_shutting_down")
    try:
        await close_pool()
        logger.info("database_pool_closed")
        logger.info("application_stopped")
    except Exception as exc:
        logger.error("application_shutdown_error", error=str(exc))


# Create FastAPI application
app = FastAPI(
    title="Digital FTE Customer Success Agent API",
    description="Multi-channel AI-powered customer support system with Groq AI",
    version=__version__,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
from .routes.health import router as health_router
from .routes.web import router as web_router
from .routes.gmail import router as gmail_router
from .routes.whatsapp import router as whatsapp_router

app.include_router(health_router, tags=["Health"])
app.include_router(web_router, prefix="/webhooks", tags=["Web Form"])
app.include_router(gmail_router, prefix="/webhooks", tags=["Gmail"])
app.include_router(whatsapp_router, prefix="/webhooks", tags=["WhatsApp"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Digital FTE Customer Success Agent API",
        "version": __version__,
        "status": "running",
        "ai_provider": settings.ai_provider,
        "model": settings.groq_model if settings.ai_provider == "groq" else settings.openai_model,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
