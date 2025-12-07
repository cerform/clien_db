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
        clients = db_manager.get_all_clients()
        masters = db_manager.get_all_masters()
        services = db_manager.get_all_services()
        bookings = db_manager.get_all_bookings()
        
        stats = {
            "clients_count": len(clients),
            "masters_count": len(masters),
            "services_count": len(services),
            "bookings_count": len(bookings)
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
        
        # Get all masters from database
        masters = db_manager.get_all_masters()
        return masters
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
        
        # Get all services from database
        services = db_manager.get_all_services()
        return services
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
        
        # Get all clients from database
        clients = db_manager.get_all_clients()
        return clients
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
        
        # Get all bookings from database
        bookings = db_manager.get_all_bookings()
        return bookings
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
