"""
Research service - Executes the deep research flow.
"""

import logging
from typing import Any, Dict

from backend.services.flow import DeepResearchFlow
from backend.services.session import session_manager


async def run_research(session_id: str, query: str):
    """
    Execute the research flow with status updates.
    
    Args:
        session_id: The research session ID
        query: The research query
    """
    try:
        logging.info(f"Starting research for session {session_id}")
        session = session_manager.get_session(session_id)
        if not session:
            logging.error(f"Session {session_id} not found")
            return
        
        session["status"] = "running"
        
        # Update search agent status
        await session_manager.update_agent_status(
            session_id, "search", "running", "Searching for relevant URLs..."
        )
        
        # Create and run the flow
        flow = DeepResearchFlow()
        flow.state.query = query
        flow.state.session_id = session_id
        
        # Broadcast flow started
        await session_manager.broadcast(session_id, {
            "type": "flow_started",
            "query": query,
        })
        
        # Run the flow
        try:
            result = await flow.kickoff_async()
            
            # Update all agents to done
            for agent_id in ["search", "instagram", "linkedin", "youtube", "x", "web", "synthesis"]:
                await session_manager.update_agent_status(session_id, agent_id, "done")
            
            # Store result
            session["result"] = result.get("result", "No result returned")
            session["status"] = "completed"
            
            await session_manager.broadcast(session_id, {
                "type": "research_complete",
                "result": session["result"],
            })
            logging.info(f"Research completed for session {session_id}")
            
        except Exception as e:
            logging.error(f"Flow execution error: {type(e).__name__}: {e}")
            session["status"] = "error"
            await session_manager.broadcast(session_id, {
                "type": "error",
                "message": str(e),
            })
            
    except Exception as e:
        logging.error(f"Research error: {e}")
        session_manager.sessions[session_id]["status"] = "error"


async def run_deep_research(prompt: str) -> str:
    """
    Run the deep research flow and return the result.
    
    Args:
        prompt: The research query
        
    Returns:
        The research result as a string
    """
    try:
        flow = DeepResearchFlow()
        flow.state.query = prompt
        payload: Dict[str, Any] = await flow.kickoff_async()
        return str(payload.get("result", "No result returned"))
    except Exception as e:
        return f"An error occurred: {e}"
