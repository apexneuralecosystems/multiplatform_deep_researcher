"""
Research API routes with rate limiting.
"""

import asyncio

from fastapi import APIRouter, HTTPException, Request

from backend.api.models import ResearchRequest, ResearchResponse
from backend.core.rate_limit import limiter
from backend.services.research import run_research
from backend.services.session import session_manager


router = APIRouter()


@router.post("/api/research", response_model=ResearchResponse)
@limiter.limit("10/minute")  # Max 10 research requests per minute per IP
async def start_research(request: Request, research_request: ResearchRequest):
    """Start a new research session."""
    if not research_request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Create session
    session_id = session_manager.create_session(research_request.query)
    
    # Start research in background
    asyncio.create_task(run_research(session_id, research_request.query))
    
    return ResearchResponse(
        session_id=session_id,
        status="started",
        message="Research session initiated. Connect to WebSocket for real-time updates.",
    )


@router.get("/api/research/{session_id}")
@limiter.limit("60/minute")  # Max 60 status checks per minute per IP
async def get_research_status(request: Request, session_id: str):
    """Get current status of a research session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "query": session["query"],
        "status": session["status"],
        "agents": session["agents"],
        "result": session["result"],
    }

