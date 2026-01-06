"""
Multiplatform Deep Researcher - FastAPI Backend
MCP-Powered Agentic Intelligence System

Run with: uvicorn backend.main:app --reload --port 8000
Production: gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.core.rate_limit import limiter

# Initialize logging (import triggers setup)
from backend.core.logging import logger

from backend.api.routes import health, research
from backend.api import websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("🚀 Deep Researcher API starting...")
    logger.info(f"   CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"   MCP Mode: {settings.MCP_MODE}")
    logger.info(f"   Debug: {settings.DEBUG}")
    yield
    # Shutdown
    logger.info("👋 Deep Researcher API shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Multiplatform Deep Researcher API",
    description="MCP-Powered Agentic Intelligence System",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(research.router)
app.include_router(websocket.router)


# ─────────────────────────────────────────────────────────────
# Run with: uvicorn backend.main:app --reload --port 8000
# Production: gunicorn backend.main:app -w 1 -k uvicorn.workers.UvicornWorker
# ─────────────────────────────────────────────────────────────
