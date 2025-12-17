"""Health check endpoints"""

from datetime import datetime
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    """
    Simple health check endpoint

    Returns service status and timestamp.
    """
    return {
        "status": "healthy",
        "service": "SCORE™ Engine",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness probe for Kubernetes/ECS

    Checks if the service is ready to accept traffic.
    """
    # In production, check database connection, Redis, etc.
    return {
        "ready": True,
        "checks": {
            "database": "ok",  # TODO: Actual DB check
            "redis": "ok",     # TODO: Actual Redis check
            "config": "ok",
        }
    }
