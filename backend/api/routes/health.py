"""
Health check routes with proper timeout and dependency checks.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

import httpx
from fastapi import APIRouter

from backend.core.config import settings


router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Multiplatform Deep Researcher",
        "version": "1.0.0",
        "status": "operational",
    }


@router.get("/api/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/api/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check with dependency verification.
    Includes timeout protection for external service checks.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check OpenRouter API connectivity (with timeout)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
            )
            health_status["checks"]["openrouter"] = {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "response_time_ms": response.elapsed.total_seconds() * 1000 if response.elapsed else None
            }
    except asyncio.TimeoutError:
        health_status["checks"]["openrouter"] = {"status": "timeout", "error": "Request timed out"}
        health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["openrouter"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check MCP mode
    health_status["checks"]["mcp"] = {
        "status": "healthy",
        "mode": settings.MCP_MODE
    }
    
    # Memory check (basic)
    try:
        import psutil
        memory = psutil.virtual_memory()
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory.percent < 90 else "warning",
            "percent_used": memory.percent
        }
    except ImportError:
        health_status["checks"]["memory"] = {"status": "unavailable", "note": "psutil not installed"}
    
    return health_status


@router.get("/api/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe.
    Returns 200 if the service is ready to accept traffic.
    """
    # Check if critical configuration is present
    if not settings.OPENROUTER_API_KEY:
        return {"ready": False, "reason": "OPENROUTER_API_KEY not configured"}
    
    return {"ready": True}


@router.get("/api/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    Returns 200 if the service is alive.
    """
    return {"alive": True}
