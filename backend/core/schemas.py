"""
Shared Pydantic schemas used across the application.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Platform Types
# ─────────────────────────────────────────────────────────────

Platform = Literal["instagram", "linkedin", "youtube", "x", "web"]


# ─────────────────────────────────────────────────────────────
# Research Flow Schemas
# ─────────────────────────────────────────────────────────────

class URLBuckets(BaseModel):
    """URLs organized by platform."""
    instagram: List[str] = Field(default_factory=list)
    linkedin: List[str] = Field(default_factory=list)
    youtube: List[str] = Field(default_factory=list)
    x: List[str] = Field(default_factory=list)
    web: List[str] = Field(default_factory=list)


class SpecialistOutput(BaseModel):
    """Output from a platform specialist agent."""
    platform: Platform
    url: str
    summary: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeepResearchFlowState(BaseModel):
    """State for the deep research flow."""
    query: str = ""
    final_response: Optional[str] = None
