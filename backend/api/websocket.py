"""
WebSocket endpoint for real-time research updates.
"""

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.session import session_manager

logger = logging.getLogger(__name__)


router = APIRouter()


@router.websocket("/ws/research/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time agent status updates."""
    logger.info(f"WebSocket connection attempt for session {session_id}")
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for session {session_id}")
    session_manager.register_websocket(session_id, websocket)
    
    try:
        # Send initial state
        session = session_manager.get_session(session_id)
        if session:
            logger.info(f"Sending initial state to session {session_id}")
            await websocket.send_json({
                "type": "initial_state",
                "agents": session["agents"],
            })
        else:
            logger.warning(f"Session {session_id} not found when sending initial state")
        
        # Keep connection alive and listen for messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle ping/pong for keep-alive
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        session_manager.unregister_websocket(session_id)
