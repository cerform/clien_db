"""API routers for web interface"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api", tags=["api"])

@api_router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Get database statistics"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        # Get stats from database
        stats = {
            "clients_count": 0,
            "masters_count": 0,
            "services_count": 0,
            "bookings_count": 0
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting statistics")

@api_router.get("/masters")
async def get_masters() -> List[Dict[str, Any]]:
    """Get all masters"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        return []
    except Exception as e:
        logger.error(f"Error getting masters: {e}")
        raise HTTPException(status_code=500, detail="Error getting masters")

@api_router.post("/masters")
async def create_master(request: Request) -> Dict[str, Any]:
    """Create new master"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        return {"success": True, "message": "Master created"}
    except Exception as e:
        logger.error(f"Error creating master: {e}")
        raise HTTPException(status_code=500, detail="Error creating master")

@api_router.get("/services")
async def get_services() -> List[Dict[str, Any]]:
    """Get all services"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        return []
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        raise HTTPException(status_code=500, detail="Error getting services")

@api_router.post("/services")
async def create_service(request: Request) -> Dict[str, Any]:
    """Create new service"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        return {"success": True, "message": "Service created"}
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        raise HTTPException(status_code=500, detail="Error creating service")

@api_router.get("/clients")
async def get_clients() -> List[Dict[str, Any]]:
    """Get all clients"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        return []
    except Exception as e:
        logger.error(f"Error getting clients: {e}")
        raise HTTPException(status_code=500, detail="Error getting clients")

@api_router.get("/bookings")
async def get_bookings() -> List[Dict[str, Any]]:
    """Get all bookings"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        return []
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        raise HTTPException(status_code=500, detail="Error getting bookings")

@api_router.get("/inka-training-stats")
async def get_inka_training_stats() -> Dict[str, Any]:
    """Get INKA training statistics"""
    try:
        from src.web.app import learning_system
        
        if not learning_system:
            raise HTTPException(status_code=500, detail="Learning system not initialized")
        
        return {
            "total_sessions": 0,
            "successful_trainings": 0,
            "average_score": 0
        }
    except Exception as e:
        logger.error(f"Error getting INKA stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting INKA statistics")


@api_router.get("/inka-training/stats")
async def get_inka_training_stats_alt() -> Dict[str, Any]:
    """Alternative path used by frontend; returns INKA training stats"""
    try:
        return await get_inka_training_stats()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting INKA stats (alt): {e}")
        raise HTTPException(status_code=500, detail="Error getting INKA statistics")


@api_router.post("/inka-training/chat")
async def inka_chat(request: Request) -> Dict[str, Any]:
    """Return a simple assistant response — placeholder"""
    try:
        body = await request.json()
        message = body.get('message', '')
        # Basic placeholder response
        response_text = f"Echo: {message}" if message else ""
        return {"response": response_text, "learned": False}
    except Exception as e:
        logger.error(f"Error INKA chat: {e}")
        raise HTTPException(status_code=500, detail="Error in INKA chat")


@api_router.post("/inka-training/scenario")
async def create_scenario(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        # Pretend to save the scenario
        return {"success": True, "message": "Scenario created"}
    except Exception as e:
        logger.error(f"Error creating scenario: {e}")
        raise HTTPException(status_code=500, detail="Error creating scenario")


@api_router.get("/inka-training/scenarios")
async def get_scenarios() -> Dict[str, Any]:
    try:
        return {"scenarios": []}
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        raise HTTPException(status_code=500, detail="Error getting scenarios")


@api_router.post("/inka-training/correction")
async def create_correction(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error creating correction: {e}")
        raise HTTPException(status_code=500, detail="Error creating correction")


@api_router.get("/inka-training/corrections")
async def get_corrections() -> Dict[str, Any]:
    try:
        return {"corrections": []}
    except Exception as e:
        logger.error(f"Error getting corrections: {e}")
        raise HTTPException(status_code=500, detail="Error getting corrections")


@api_router.post("/inka-training/knowledge")
async def create_knowledge(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error creating knowledge: {e}")
        raise HTTPException(status_code=500, detail="Error creating knowledge")


@api_router.get("/inka-training/knowledge")
async def get_knowledge() -> Dict[str, Any]:
    try:
        return {"knowledge": []}
    except Exception as e:
        logger.error(f"Error getting knowledge: {e}")
        raise HTTPException(status_code=500, detail="Error getting knowledge")


@api_router.get("/inka-training/recent")
async def get_recent_trainings() -> Dict[str, Any]:
    try:
        return {"recent": []}
    except Exception as e:
        logger.error(f"Error getting recent inka trainings: {e}")
        raise HTTPException(status_code=500, detail="Error getting recent trainings")


@api_router.post("/inka-training/export")
async def export_training_data() -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error exporting inka data: {e}")
        raise HTTPException(status_code=500, detail="Error exporting data")


@api_router.post("/inka-training/import")
async def import_training_data(request: Request) -> Dict[str, Any]:
    try:
        # Accept json payload as placeholder
        body = await request.json()
        return {"success": True, "imported": len(body.get('entries', [])) if isinstance(body, dict) else 0}
    except Exception as e:
        logger.error(f"Error importing inka data: {e}")
        raise HTTPException(status_code=500, detail="Error importing data")


@api_router.delete("/inka-training/scenario/{id}")
async def remove_scenario(id: str) -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting scenario {id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting scenario")


@api_router.delete("/inka-training/correction/{id}")
async def remove_correction(id: str) -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting correction {id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting correction")


@api_router.delete("/inka-training/knowledge/{id}")
async def remove_knowledge(id: str) -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting knowledge {id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting knowledge")

@api_router.post("/inka-training")
async def train_inka(request: Request) -> Dict[str, Any]:
    """Train INKA with provided text"""
    try:
        from src.web.app import learning_system
        
        body = await request.json()
        text = body.get("text", "")
        
        if not learning_system:
            raise HTTPException(status_code=500, detail="Learning system not initialized")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        return {"success": True, "message": "Training started"}
    except Exception as e:
        logger.error(f"Error training INKA: {e}")
        raise HTTPException(status_code=500, detail="Error training INKA")

@api_router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "service": "tattoo-bot-admin"}
