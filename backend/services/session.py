"""
Session management service.
Handles research sessions and WebSocket connections.
"""

import uuid
from typing import Any, Dict, Optional

from fastapi import WebSocket


class SessionManager:
    """Manages research sessions and WebSocket connections."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.websockets: Dict[str, WebSocket] = {}
    
    def create_session(self, query: str) -> str:
        """Create a new research session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "query": query,
            "status": "pending",
            "agents": {
                "search": {"status": "waiting", "platform": "search"},
                "instagram": {"status": "waiting", "platform": "instagram"},
                "linkedin": {"status": "waiting", "platform": "linkedin"},
                "youtube": {"status": "waiting", "platform": "youtube"},
                "x": {"status": "waiting", "platform": "x"},
                "web": {"status": "waiting", "platform": "web"},
                "synthesis": {"status": "waiting", "platform": "synthesis"},
            },
            "result": None,
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    async def update_agent_status(
        self, 
        session_id: str, 
        agent_id: str, 
        status: str, 
        message: Optional[str] = None
    ):
        """Update agent status and broadcast to WebSocket."""
        if session_id in self.sessions:
            self.sessions[session_id]["agents"][agent_id]["status"] = status
            if message:
                self.sessions[session_id]["agents"][agent_id]["message"] = message
            
            # Broadcast to connected WebSocket
            await self.broadcast(session_id, {
                "type": "agent_update",
                "agent_id": agent_id,
                "status": status,
                "message": message,
            })
    
    async def broadcast(self, session_id: str, data: Dict[str, Any]):
        """Broadcast data to WebSocket client."""
        if session_id in self.websockets:
            try:
                await self.websockets[session_id].send_json(data)
            except Exception:
                pass  # Client disconnected
    
    def register_websocket(self, session_id: str, websocket: WebSocket):
        """Register a WebSocket connection for a session."""
        self.websockets[session_id] = websocket
    
    def unregister_websocket(self, session_id: str):
        """Unregister a WebSocket connection."""
        if session_id in self.websockets:
            del self.websockets[session_id]


# Global session manager instance
session_manager = SessionManager()
