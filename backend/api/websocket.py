"""
WebSocket endpoint for real-time research updates.
"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.session import session_manager


router = APIRouter()


@router.websocket("/ws/research/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time agent status updates."""
    await websocket.accept()
    session_manager.register_websocket(session_id, websocket)
    
    try:
        # Send initial state
        session = session_manager.get_session(session_id)
        if session:
            await websocket.send_json({
                "type": "initial_state",
                "agents": session["agents"],
            })
        
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
        pass
    finally:
        session_manager.unregister_websocket(session_id)
