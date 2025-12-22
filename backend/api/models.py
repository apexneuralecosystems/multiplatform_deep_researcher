"""
Pydantic models for API request/response schemas.
"""

from typing import Optional
from pydantic import BaseModel


# ─────────────────────────────────────────────────────────────
# Request Models
# ─────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    """Request model for starting a research session."""
    query: str
    brightdata_api_key: Optional[str] = None


# ─────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────

class ResearchResponse(BaseModel):
    """Response model for research session creation."""
    session_id: str
    status: str
    message: str


class AgentStatus(BaseModel):
    """Status model for individual agents."""
    agent_id: str
    platform: str
    status: str  # "waiting", "running", "done", "error"
    message: Optional[str] = None
    progress: Optional[float] = None
