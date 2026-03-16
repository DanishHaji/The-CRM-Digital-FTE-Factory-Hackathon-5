"""Health check endpoints for monitoring - Simplified without Kafka."""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from ...database.connection import get_pool
from ...utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str
    database: str
    ai_provider: str


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    description="Check health of API and database",
)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.

    Checks:
    - API service is running
    - Database connection pool is available

    Returns:
        HealthCheckResponse with status of all components
    """
    from ...utils.config import get_settings
    settings = get_settings()

    # Check database
    database_status = "unknown"
    try:
        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            database_status = "connected"
    except Exception as exc:
        logger.error("health_check_database_failed", error=str(exc))
        database_status = f"error: {type(exc).__name__}"

    # Overall status
    overall_status = "healthy" if database_status == "connected" else "unhealthy"

    return HealthCheckResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        database=database_status,
        ai_provider=f"{settings.ai_provider} ({settings.groq_model})",
    )


@router.get(
    "/health/liveness",
    summary="Liveness probe",
    description="Kubernetes liveness probe",
)
async def liveness() -> dict:
    """Liveness probe - API is running."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/health/readiness",
    summary="Readiness probe",
    description="Kubernetes readiness probe",
)
async def readiness() -> dict:
    """Readiness probe - API can serve traffic."""
    ready = True
    checks = {}

    # Check database
    try:
        pool = await get_pool()
        if pool:
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            checks["database"] = "ready"
        else:
            checks["database"] = "not ready"
            ready = False
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"
        ready = False

    return {
        "status": "ready" if ready else "not ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
