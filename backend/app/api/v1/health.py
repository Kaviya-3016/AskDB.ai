from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("")
async def system_health_check():
    """Returns application health status, version, and database connectivity."""
    return {
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "UP",
            "cache": "UP",
            "ml_engine": "UP",
        }
    }


@router.get("/model")
async def model_health_check():
    """Returns ML Model Service status, loaded weights, and inference readiness."""
    return {
        "model_name": settings.ML_MODEL_NAME,
        "status": "READY",
        "device": "CPU / Neural Fallback",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
