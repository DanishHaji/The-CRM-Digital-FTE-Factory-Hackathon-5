"""API routes - Simplified for direct agent processing."""

# Only export the routes we're actually using
from .health import router as health_router
from .web import router as web_router

__all__ = ["health_router", "web_router"]
