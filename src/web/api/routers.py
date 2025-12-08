"""API routers for web interface"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api", tags=["api"])


# ================== STATISTICS ==================

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
        
        # Calculate additional stats
        active_bookings = [b for b in bookings if b.get("status") in ["pending", "confirmed"]]
        completed_bookings = [b for b in bookings if b.get("status") == "completed"]
        
        # Calculate revenue
        total_revenue = sum(float(b.get("price", 0) or 0) for b in completed_bookings)
        
        stats = {
            "clients_count": len(clients),
            "masters_count": len(masters),
            "services_count": len(services),
            "bookings_count": len(bookings),
            "active_bookings": len(active_bookings),
            "completed_bookings": len(completed_bookings),
            "total_revenue": total_revenue,
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting statistics")


@api_router.get("/analytics")
async def get_analytics() -> Dict[str, Any]:
    """Get detailed analytics"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        bookings = db_manager.get_all_bookings()
        clients = db_manager.get_all_clients()
        masters = db_manager.get_all_masters()
        
        # Bookings by status
        status_counts = {}
        for b in bookings:
            status = b.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Bookings by master
        master_bookings = {}
        for b in bookings:
            master_id = b.get("master_id", "unknown")
            master_bookings[master_id] = master_bookings.get(master_id, 0) + 1
        
        # Top masters by bookings
        top_masters = sorted(master_bookings.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Revenue by month (last 6 months)
        completed = [b for b in bookings if b.get("status") == "completed"]
        revenue_by_month = {}
        for b in completed:
            date_str = b.get("date", "")
            if date_str:
                try:
                    month_key = date_str[:7]  # YYYY-MM
                    price = float(b.get("price", 0) or 0)
                    revenue_by_month[month_key] = revenue_by_month.get(month_key, 0) + price
                except:
                    pass
        
        # New clients this month
        current_month = datetime.now().strftime("%Y-%m")
        new_clients_this_month = sum(
            1 for c in clients 
            if c.get("created_at", "").startswith(current_month)
        )
        
        return {
            "status_distribution": status_counts,
            "bookings_by_master": dict(top_masters),
            "revenue_by_month": revenue_by_month,
            "new_clients_this_month": new_clients_this_month,
            "total_clients": len(clients),
            "total_bookings": len(bookings),
            "conversion_rate": round(len(bookings) / max(len(clients), 1) * 100, 1),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail="Error getting analytics")


# ================== MASTERS ==================

@api_router.get("/masters")
async def get_masters() -> List[Dict[str, Any]]:
    """Get all masters"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        masters = db_manager.get_all_masters()
        return masters
    except Exception as e:
        logger.error(f"Error getting masters: {e}")
        raise HTTPException(status_code=500, detail="Error getting masters")


@api_router.get("/masters/{master_id}")
async def get_master(master_id: str) -> Dict[str, Any]:
    """Get master by ID"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        masters = db_manager.get_all_masters()
        for master in masters:
            if master.get("id") == master_id:
                return master
        
        raise HTTPException(status_code=404, detail="Master not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting master: {e}")
        raise HTTPException(status_code=500, detail="Error getting master")


@api_router.post("/masters")
async def create_master(request: Request) -> Dict[str, Any]:
    """Create new master"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        # Validate required fields
        required_fields = ["name", "specialization", "phone"]
        for field in required_fields:
            if not body.get(field):
                raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
        
        success, message = db_manager.add_master(body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating master: {e}")
        raise HTTPException(status_code=500, detail="Error creating master")


@api_router.put("/masters/{master_id}")
async def update_master(master_id: str, request: Request) -> Dict[str, Any]:
    """Update existing master"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.edit_master(master_id, body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating master: {e}")
        raise HTTPException(status_code=500, detail="Error updating master")


@api_router.delete("/masters/{master_id}")
async def delete_master(master_id: str) -> Dict[str, Any]:
    """Delete master"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.delete_master(master_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting master: {e}")
        raise HTTPException(status_code=500, detail="Error deleting master")


# ================== SERVICES ==================

@api_router.get("/services")
async def get_services() -> List[Dict[str, Any]]:
    """Get all services"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        services = db_manager.get_all_services()
        return services
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        raise HTTPException(status_code=500, detail="Error getting services")


@api_router.get("/services/{service_id}")
async def get_service(service_id: str) -> Dict[str, Any]:
    """Get service by ID"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        services = db_manager.get_all_services()
        for service in services:
            if service.get("id") == service_id:
                return service
        
        raise HTTPException(status_code=404, detail="Service not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service: {e}")
        raise HTTPException(status_code=500, detail="Error getting service")


@api_router.post("/services")
async def create_service(request: Request) -> Dict[str, Any]:
    """Create new service"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        # Validate required fields
        required_fields = ["name", "duration", "price"]
        for field in required_fields:
            if not body.get(field):
                raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
        
        success, message = db_manager.add_service(body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        raise HTTPException(status_code=500, detail="Error creating service")


@api_router.put("/services/{service_id}")
async def update_service(service_id: str, request: Request) -> Dict[str, Any]:
    """Update existing service"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.edit_service(service_id, body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating service: {e}")
        raise HTTPException(status_code=500, detail="Error updating service")


@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str) -> Dict[str, Any]:
    """Delete service"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.delete_service(service_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting service: {e}")
        raise HTTPException(status_code=500, detail="Error deleting service")


# ================== CLIENTS ==================

@api_router.get("/clients")
async def get_clients() -> List[Dict[str, Any]]:
    """Get all clients"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        clients = db_manager.get_all_clients()
        return clients
    except Exception as e:
        logger.error(f"Error getting clients: {e}")
        raise HTTPException(status_code=500, detail="Error getting clients")


@api_router.get("/clients/{client_id}")
async def get_client(client_id: str) -> Dict[str, Any]:
    """Get client by ID"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        clients = db_manager.get_all_clients()
        for client in clients:
            if client.get("id") == client_id:
                # Get client's bookings
                bookings = db_manager.get_all_bookings()
                client_bookings = [b for b in bookings if b.get("client_id") == client_id]
                client["bookings"] = client_bookings
                client["total_bookings"] = len(client_bookings)
                client["total_spent"] = sum(float(b.get("price", 0) or 0) for b in client_bookings if b.get("status") == "completed")
                return client
        
        raise HTTPException(status_code=404, detail="Client not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client: {e}")
        raise HTTPException(status_code=500, detail="Error getting client")


@api_router.post("/clients")
async def create_client(request: Request) -> Dict[str, Any]:
    """Create new client"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        # Validate required fields
        required_fields = ["name", "phone"]
        for field in required_fields:
            if not body.get(field):
                raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
        
        success, message = db_manager.add_client(body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        raise HTTPException(status_code=500, detail="Error creating client")


@api_router.put("/clients/{client_id}")
async def update_client(client_id: str, request: Request) -> Dict[str, Any]:
    """Update existing client"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.edit_client(client_id, body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating client: {e}")
        raise HTTPException(status_code=500, detail="Error updating client")


@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str) -> Dict[str, Any]:
    """Delete client"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.delete_client(client_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting client: {e}")
        raise HTTPException(status_code=500, detail="Error deleting client")


# ================== BOOKINGS ==================

@api_router.get("/bookings")
async def get_bookings(
    status: Optional[str] = None,
    master_id: Optional[str] = None,
    client_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get all bookings with client and master names"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        bookings = db_manager.get_all_bookings()
        clients = db_manager.get_all_clients()
        masters = db_manager.get_all_masters()
        client_map = {c.get("id"): c.get("name", "Client") for c in clients}
        master_map = {m.get("id"): m.get("name", "Мастер") for m in masters}
        
        # Apply filters
        if status:
            bookings = [b for b in bookings if b.get("status") == status]
        if master_id:
            bookings = [b for b in bookings if b.get("master_id") == master_id]
        if client_id:
            bookings = [b for b in bookings if b.get("client_id") == client_id]
        if date_from:
            bookings = [b for b in bookings if b.get("date", "") >= date_from]
        if date_to:
            bookings = [b for b in bookings if b.get("date", "") <= date_to]
        
        # Sort by date descending
        bookings.sort(key=lambda x: (x.get("date", ""), x.get("time", "")), reverse=True)
        
        # Добавляем имена
        for b in bookings:
            b["client_name"] = client_map.get(b.get("client_id"), "Client")
            b["master_name"] = master_map.get(b.get("master_id"), "Мастер")
        
        return bookings
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        raise HTTPException(status_code=500, detail="Error getting bookings")


@api_router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str) -> Dict[str, Any]:
    """Get booking by ID"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        bookings = db_manager.get_all_bookings()
        for booking in bookings:
            if booking.get("id") == booking_id:
                return booking
        
        raise HTTPException(status_code=404, detail="Booking not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting booking: {e}")
        raise HTTPException(status_code=500, detail="Error getting booking")


@api_router.post("/bookings")
async def create_booking(request: Request) -> Dict[str, Any]:
    """Create new booking"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        # Validate required fields
        required_fields = ["client_id", "master_id", "service_id", "date", "time"]
        for field in required_fields:
            if not body.get(field):
                raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
        
        success, message = db_manager.add_booking(body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail="Error creating booking")


@api_router.put("/bookings/{booking_id}")
async def update_booking(booking_id: str, request: Request) -> Dict[str, Any]:
    """Update existing booking"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.edit_booking(booking_id, body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating booking: {e}")
        raise HTTPException(status_code=500, detail="Error updating booking")


@api_router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, request: Request) -> Dict[str, Any]:
    """Cancel booking"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        # Get reason from request body if provided
        reason = ""
        try:
            body = await request.json()
            reason = body.get("reason", "")
        except:
            pass
        
        success, message = db_manager.cancel_booking(booking_id, reason)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling booking: {e}")
        raise HTTPException(status_code=500, detail="Error canceling booking")


@api_router.post("/bookings/{booking_id}/confirm")
async def confirm_booking(booking_id: str) -> Dict[str, Any]:
    """Confirm booking"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.confirm_booking(booking_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming booking: {e}")
        raise HTTPException(status_code=500, detail="Error confirming booking")


@api_router.post("/bookings/{booking_id}/complete")
async def complete_booking(booking_id: str) -> Dict[str, Any]:
    """Mark booking as completed"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.complete_booking(booking_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing booking: {e}")
        raise HTTPException(status_code=500, detail="Error completing booking")


# ================== INKA TRAINING ==================

@api_router.get("/inka-training-stats")
async def get_inka_training_stats() -> Dict[str, Any]:
    """Get INKA training statistics"""
    try:
        from src.web.app import learning_system
        
        if not learning_system:
            # Return empty stats if not initialized
            return {
                "total_sessions": 0,
                "successful_trainings": 0,
                "average_score": 0,
                "categories": {},
                "message": "Learning system not initialized"
            }
        
        stats = learning_system.get_training_stats()
        return {
            "total_sessions": stats.get("total_examples", 0),
            "successful_trainings": stats.get("total_improvements", 0),
            "average_score": 0,
            "categories": stats.get("categories", {}),
            "improvement_rate": stats.get("improvement_rate", "0%")
        }
    except Exception as e:
        logger.error(f"Error getting INKA stats: {e}")
        return {
            "total_sessions": 0,
            "successful_trainings": 0,
            "average_score": 0,
            "error": str(e)
        }


@api_router.post("/inka-training")
async def train_inka(request: Request) -> Dict[str, Any]:
    """Train INKA with provided text"""
    try:
        from src.web.app import learning_system
        
        body = await request.json()
        text = body.get("text", "")
        category = body.get("category", "general")
        correction = body.get("correction", "")
        tags = body.get("tags", "")
        
        if not learning_system:
            raise HTTPException(status_code=500, detail="Learning system not initialized")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        success, message = learning_system.add_training_example(
            category=category,
            user_input=text,
            inka_response="",
            correction=correction,
            tags=tags
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training INKA: {e}")
        raise HTTPException(status_code=500, detail="Error training INKA")


@api_router.get("/inka-training-examples")
async def get_training_examples(
    category: Optional[str] = None,
    tag: Optional[str] = None
) -> Dict[str, Any]:
    """Get INKA training examples"""
    try:
        from src.web.app import learning_system
        
        if not learning_system:
            return {"total": 0, "examples": []}
        
        result = learning_system.get_training_examples(category=category or "", tag=tag or "")
        return result
    except Exception as e:
        logger.error(f"Error getting training examples: {e}")
        raise HTTPException(status_code=500, detail="Error getting training examples")


# ================== SCHEDULE ==================

@api_router.get("/schedule")
async def get_schedule(master_id: Optional[str] = None) -> Dict[str, Any]:
    """Get schedule"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        result = db_manager.get_schedule(master_id or "")
        return result
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        raise HTTPException(status_code=500, detail="Error getting schedule")


@api_router.post("/schedule")
async def create_schedule_entry(request: Request) -> Dict[str, Any]:
    """Create schedule entry"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.add_schedule_entry(body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating schedule entry: {e}")
        raise HTTPException(status_code=500, detail="Error creating schedule entry")


@api_router.put("/schedule/{entry_id}")
async def update_schedule_entry(entry_id: str, request: Request) -> Dict[str, Any]:
    """Update schedule entry"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.update_schedule_entry(entry_id, body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating schedule entry: {e}")
        raise HTTPException(status_code=500, detail="Error updating schedule entry")


@api_router.delete("/schedule/{entry_id}")
async def delete_schedule_entry(entry_id: str) -> Dict[str, Any]:
    """Delete schedule entry"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        success, message = db_manager.delete_schedule_entry(entry_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting schedule entry: {e}")
        raise HTTPException(status_code=500, detail="Error deleting schedule entry")


# ================== GOOGLE CALENDAR ==================

@api_router.get("/calendar/salon")
async def get_salon_calendar(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get salon calendar (all masters working days)"""
    try:
        from src.web.app import db_manager
        from src.config import config
        from datetime import datetime, timedelta
        
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        masters = db_manager.get_all_masters() if db_manager else []
        
        # Get all masters' working days
        salon_events = []
        for master in masters:
            if master.get("status") != "active":
                continue
            
            calendar_id = master.get("calendar_id")
            if calendar_id:
                try:
                    from src.calendars.google_calendar_sync import GoogleCalendarSync
                    
                    credentials_file = getattr(config, 'google_credentials_file', 'credentials.json')
                    calendar = GoogleCalendarSync(credentials_file, calendar_id)
                    events = calendar.get_events(start_date, end_date)
                    
                    for event in events:
                        salon_events.append({
                            "id": event.get("id"),
                            "title": f"{master.get('name')}: {event.get('summary', 'Занято')}",
                            "master_id": master.get("id"),
                            "master_name": master.get("name"),
                            "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
                            "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                            "color": master.get("color", "#667eea")
                        })
                except Exception as e:
                    logger.warning(f"Calendar error for master {master.get('name')}: {e}")
        
        return {
            "events": salon_events,
            "start_date": start_date,
            "end_date": end_date
        }
    except Exception as e:
        logger.error(f"Error getting salon calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/calendar/master/{master_id}")
async def get_master_calendar(master_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """Get master's calendar with bookings"""
    try:
        from src.web.app import db_manager
        from src.config import config
        from datetime import datetime, timedelta
        
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get master data
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        events = []
        calendar_id = master.get("calendar_id")
        
        if calendar_id:
            try:
                from src.calendars.google_calendar_sync import GoogleCalendarSync
                
                credentials_file = getattr(config, 'google_credentials_file', 'credentials.json')
                calendar = GoogleCalendarSync(credentials_file, calendar_id)
                google_events = calendar.get_events(start_date, end_date)
                
                for event in google_events:
                    events.append({
                        "id": event.get("id"),
                        "title": event.get("summary", "Занято"),
                        "start": event.get("start", {}).get("dateTime") or event.get("start", {}).get("date"),
                        "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                        "description": event.get("description", ""),
                        "source": "google_calendar"
                    })
            except Exception as e:
                logger.warning(f"Google Calendar error: {e}")
        
        # Also get bookings from database
        bookings = db_manager.get_all_bookings()
        clients = db_manager.get_all_clients()
        services = db_manager.get_all_services()
        
        for booking in bookings:
            if booking.get("master_id") != master_id:
                continue
            if booking.get("status") == "cancelled":
                continue
            
            date = booking.get("date", "")
            time = booking.get("time", "10:00")
            
            if not date:
                continue
                
            client = next((c for c in clients if c.get("id") == booking.get("client_id")), {})
            service = next((s for s in services if s.get("id") == booking.get("service_id")), {})
            
            status_colors = {
                "pending": "#ffc107",
                "confirmed": "#17a2b8", 
                "completed": "#28a745",
                "cancelled": "#dc3545"
            }
            
            events.append({
                "id": f"booking_{booking.get('id')}",
                "title": f"{client.get('name', 'Клиент')} - {service.get('name', 'Услуга')}",
                "start": f"{date}T{time}:00",
                "end": f"{date}T{int(time.split(':')[0])+1}:{time.split(':')[1]}:00" if ':' in time else f"{date}T{int(time)+1}:00:00",
                "client_name": client.get("name"),
                "client_phone": client.get("phone"),
                "service_name": service.get("name"),
                "price": booking.get("price"),
                "status": booking.get("status"),
                "color": status_colors.get(booking.get("status"), "#667eea"),
                "source": "database"
            })
        
        return {
            "master": {
                "id": master.get("id"),
                "name": master.get("name"),
                "calendar_id": calendar_id
            },
            "events": events,
            "start_date": start_date,
            "end_date": end_date
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting master calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calendar/event")
async def create_calendar_event(request: Request) -> Dict[str, Any]:
    """Create a calendar event for a master"""
    try:
        from src.web.app import db_manager
        from src.config import config
        from datetime import datetime
        
        body = await request.json()
        master_id = body.get("master_id")
        title = body.get("title")
        start_time = body.get("start_time")  # ISO format
        duration = body.get("duration", 60)  # minutes
        
        if not all([master_id, title, start_time]):
            raise HTTPException(status_code=400, detail="Missing required fields: master_id, title, start_time")
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        calendar_id = master.get("calendar_id")
        if not calendar_id:
            raise HTTPException(status_code=400, detail="Master has no calendar configured")
        
        from src.calendars.google_calendar_sync import GoogleCalendarSync
        
        credentials_file = getattr(config, 'google_credentials_file', 'credentials.json')
        calendar = GoogleCalendarSync(credentials_file, calendar_id)
        
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        success = calendar.create_event(title, start_dt, duration)
        
        if success:
            return {"success": True, "message": "Event created"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create event")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== CALENDAR SYNC ==================

@api_router.get("/calendar/sync/{master_id}")
async def get_sync_status(master_id: str) -> Dict[str, Any]:
    """Get synchronization status for master's calendar and schedule"""
    try:
        from src.web.app import db_manager
        from src.config import config
        from datetime import datetime, timedelta
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get master
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        calendar_id = master.get("calendar_id")
        
        # Get schedule from DB
        schedule_data = db_manager.get_schedule(master_id)
        db_schedule = schedule_data.get("schedule", [])
        
        # Get events from Google Calendar (next 7 days)
        calendar_events = []
        if calendar_id:
            try:
                from src.calendars.google_calendar_sync import GoogleCalendarSync
                credentials_file = getattr(config, 'google_credentials_file', 'credentials.json')
                calendar = GoogleCalendarSync(credentials_file, calendar_id)
                
                start_date = datetime.now().strftime("%Y-%m-%d")
                end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                calendar_events = calendar.get_events(start_date, end_date) or []
            except Exception as e:
                logger.warning(f"Failed to fetch calendar events: {e}")
        
        # Get bookings from DB for this master
        all_bookings = db_manager.get_all_bookings()
        db_bookings = [b for b in all_bookings if b.get("master_id") == master_id]
        
        # Calculate sync status
        return {
            "master_id": master_id,
            "master_name": master.get("name"),
            "calendar_connected": bool(calendar_id),
            "calendar_id": calendar_id,
            "db_schedule_entries": len(db_schedule),
            "calendar_events": len(calendar_events),
            "db_bookings": len(db_bookings),
            "schedule": db_schedule,
            "events": calendar_events[:20],
            "bookings": db_bookings[:20]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/calendar/sync/{master_id}")
async def sync_calendar_to_schedule(master_id: str, request: Request) -> Dict[str, Any]:
    """Sync master's Google Calendar to Schedule table"""
    try:
        from src.web.app import db_manager
        from src.config import config
        from datetime import datetime, timedelta
        import uuid
        
        body = await request.json()
        action = body.get("action", "preview")  # preview, sync_to_db, sync_to_calendar
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get master
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        calendar_id = master.get("calendar_id")
        if not calendar_id:
            raise HTTPException(status_code=400, detail="Master has no calendar configured")
        
        # Get current schedule from DB
        schedule_data = db_manager.get_schedule(master_id)
        db_schedule = schedule_data.get("schedule", [])
        
        # Get events from Google Calendar
        from src.calendars.google_calendar_sync import GoogleCalendarSync
        credentials_file = getattr(config, 'google_credentials_file', 'credentials.json')
        calendar = GoogleCalendarSync(credentials_file, calendar_id)
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        calendar_events = calendar.get_events(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")) or []
        
        # Analyze working hours from calendar events
        working_days = {}
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for event in calendar_events:
            event_start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            event_end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
            summary = event.get("summary", "").lower()
            
            # Skip if it's a booking/appointment (contains client name or specific keywords)
            skip_keywords = ["клиент", "запись", "тату", "сеанс", "консультация", "booking"]
            if any(kw in summary for kw in skip_keywords):
                continue
            
            # Check if it's a "working day" event
            work_keywords = ["работа", "work", "рабочий", "рабочее время", "working"]
            is_work_event = any(kw in summary for kw in work_keywords) or "work" in event.get("colorId", "")
            
            if event_start and "T" in str(event_start):
                try:
                    start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00')) if event_end and "T" in str(event_end) else start_dt + timedelta(hours=8)
                    
                    day_name = day_names[start_dt.weekday()]
                    start_time = start_dt.strftime("%H:%M")
                    end_time = end_dt.strftime("%H:%M")
                    
                    if day_name not in working_days:
                        working_days[day_name] = {"start": start_time, "end": end_time, "is_working": "TRUE"}
                    else:
                        # Extend hours if needed
                        if start_time < working_days[day_name]["start"]:
                            working_days[day_name]["start"] = start_time
                        if end_time > working_days[day_name]["end"]:
                            working_days[day_name]["end"] = end_time
                except Exception as e:
                    logger.warning(f"Failed to parse event time: {e}")
        
        if action == "preview":
            return {
                "success": True,
                "action": "preview",
                "current_schedule": db_schedule,
                "detected_working_days": working_days,
                "calendar_events_count": len(calendar_events),
                "message": f"Обнаружено {len(working_days)} рабочих дней из календаря"
            }
        
        elif action == "sync_to_db":
            # Create/update schedule entries in DB
            updated = 0
            created = 0
            
            for day_name, hours in working_days.items():
                # Check if entry exists
                existing = next((s for s in db_schedule if s.get("day_of_week") == day_name), None)
                
                if existing:
                    # Update existing
                    try:
                        db_manager.update_schedule_entry(existing.get("id"), {
                            "start_time": hours["start"],
                            "end_time": hours["end"],
                            "is_working": "TRUE"
                        })
                        updated += 1
                    except Exception as e:
                        logger.warning(f"Failed to update schedule entry: {e}")
                else:
                    # Create new
                    try:
                        new_entry = {
                            "id": str(uuid.uuid4()),
                            "master_id": master_id,
            
            return {
                "success": True,
                "action": "sync_to_db",
                "updated": updated,
                "created": created,
                "message": f"Синхронизировано! Обновлено: {updated}, Создано: {created}"
            }
        
        elif action == "create_default_schedule":
            # Create default 7-day schedule
            default_hours = body.get("default_hours", {"start": "10:00", "end": "19:00"})
            working_days_list = body.get("working_days", ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"])
            
            created = 0
            for day_name in day_names:
                # Check if exists
                existing = next((s for s in db_schedule if s.get("day_of_week") == day_name), None)
                if not existing:
                    is_working = "TRUE" if day_name in working_days_list else "FALSE"
                    try:
                        new_entry = {
                            "id": str(uuid.uuid4()),
                            "master_id": master_id,
                            "day_of_week": day_name,
                            "start_time": default_hours["start"],
                            "end_time": default_hours["end"],
                            "is_working": is_working
                        }
                        db_manager.add_schedule_entry(new_entry)
                        created += 1
                    except Exception as e:
                        logger.warning(f"Failed to create schedule entry: {e}")
            
            return {
                "success": True,
                "action": "create_default_schedule",
                "created": created,
                "message": f"Создано {created} записей расписания"
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== SETTINGS ==================

@api_router.get("/settings/salon-calendar")
async def get_salon_calendar() -> Dict[str, Any]:
    """Get salon calendar settings"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Try to get from settings sheet
        try:
            data = db_manager.sheets.get_sheet_values("Настройки", "A:C")
            for row in data:
                if len(row) > 1 and row[0] == "Календарь салона":
                    return {"calendar_id": row[1]}
        except:
            pass
        
        return {"calendar_id": ""}
    except Exception as e:
        logger.error(f"Error getting salon calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/settings/salon-calendar")
async def save_salon_calendar(request: Request) -> Dict[str, Any]:
    """Save salon calendar settings"""
    try:
        from src.web.app import db_manager
        
        body = await request.json()
        calendar_id = body.get("calendar_id", "")
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Try to update settings sheet
        try:
            data = db_manager.sheets.get_sheet_values("Настройки", "A:C")
            row_idx = None
            
            for i, row in enumerate(data):
                if len(row) > 0 and row[0] == "Календарь салона":
                    row_idx = i
                    break
            
            if row_idx is not None:
                # Update existing row
                db_manager.sheets.update_range("Настройки", f"B{row_idx+1}", [[calendar_id]])
            else:
                # Add new row
                db_manager.sheets.append_rows("Настройки", [["Календарь салона", calendar_id, "ID Google Calendar для общего календаря салона"]])
            
            return {"success": True, "message": "Настройки сохранены"}
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return {"success": False, "detail": str(e)}
            
    except Exception as e:
        logger.error(f"Error saving salon calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/calendar/availability/{master_id}")
async def get_master_availability(master_id: str, date: str) -> Dict[str, Any]:
    """Get available time slots for a master on a specific date"""
    try:
        from src.web.app import db_manager
        from src.config import config
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        # Working hours (default)
        all_slots = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
        busy_slots = set()
        
        calendar_id = master.get("calendar_id")
        if calendar_id:
            try:
                from src.calendars.google_calendar_sync import GoogleCalendarSync
                
                credentials_file = getattr(config, 'google_credentials_file', 'credentials.json')
                calendar = GoogleCalendarSync(credentials_file, calendar_id)
                events = calendar.get_events(date, date)
                
                for event in events:
                    start = event.get("start", {}).get("dateTime", "")
                    if start:
                        hour = start[11:16]  # Extract HH:MM
                        busy_slots.add(hour)
            except Exception as e:
                logger.warning(f"Calendar error: {e}")
        
        # Also check bookings
        bookings = db_manager.get_all_bookings()
        for booking in bookings:
            if booking.get("master_id") == master_id and booking.get("date") == date:
                if booking.get("status") not in ["cancelled"]:
                    time = booking.get("time", "")
                    if time:
                        busy_slots.add(time[:5] if len(time) > 5 else time)
        
        available_slots = [slot for slot in all_slots if slot not in busy_slots]
        
        return {
            "master_id": master_id,
            "date": date,
            "available_slots": available_slots,
            "busy_slots": list(busy_slots)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== INKA INTERACTIVE TRAINING ==================

def _get_inka_training_sheet():
    """Get or create INKA training sheet"""
    from src.web.app import sheets_client
    if not sheets_client:
        return None
    return sheets_client

def _ensure_training_sheets():
    """Ensure training sheets exist"""
    sheets_client = _get_inka_training_sheet()
    if not sheets_client:
        return False
    
    try:
        # Check if INKA_Training sheet exists
        metadata = sheets_client.service.spreadsheets().get(
            spreadsheetId=sheets_client.spreadsheet_id
        ).execute()
        
        existing_sheets = [s['properties']['title'] for s in metadata.get('sheets', [])]
        
        # Create sheets if needed
        requests = []
        for sheet_name in ['INKA_Knowledge', 'INKA_Scenarios', 'INKA_Corrections', 'INKA_Sessions']:
            if sheet_name not in existing_sheets:
                requests.append({
                    'addSheet': {
                        'properties': {'title': sheet_name}
                    }
                })
        
        if requests:
            sheets_client.service.spreadsheets().batchUpdate(
                spreadsheetId=sheets_client.spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
            # Add headers
            headers = {
                'INKA_Knowledge': ['id', 'type', 'title', 'content', 'created_at'],
                'INKA_Scenarios': ['id', 'category', 'trigger', 'response', 'context', 'created_at'],
                'INKA_Corrections': ['id', 'wrong_response', 'correct_response', 'reason', 'created_at'],
                'INKA_Sessions': ['id', 'type', 'summary', 'data', 'timestamp']
            }
            
            for sheet_name, header_row in headers.items():
                if sheet_name not in existing_sheets:
                    sheets_client.service.spreadsheets().values().update(
                        spreadsheetId=sheets_client.spreadsheet_id,
                        range=f"{sheet_name}!A1",
                        valueInputOption="RAW",
                        body={"values": [header_row]}
                    ).execute()
        
        return True
    except Exception as e:
        logger.error(f"Error ensuring training sheets: {e}")
        return False


@api_router.get("/inka-training/stats")
async def get_inka_interactive_stats() -> Dict[str, Any]:
    """Get interactive training statistics"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            return {"total_sessions": 0, "total_knowledge": 0, "total_corrections": 0}
        
        _ensure_training_sheets()
        
        knowledge = sheets_client.get_all_rows("INKA_Knowledge")
        scenarios = sheets_client.get_all_rows("INKA_Scenarios")
        corrections = sheets_client.get_all_rows("INKA_Corrections")
        sessions = sheets_client.get_all_rows("INKA_Sessions")
        
        return {
            "total_sessions": max(0, len(sessions) - 1),
            "total_knowledge": max(0, len(knowledge) - 1) + max(0, len(scenarios) - 1),
            "total_corrections": max(0, len(corrections) - 1)
        }
    except Exception as e:
        logger.error(f"Error getting training stats: {e}")
        return {"total_sessions": 0, "total_knowledge": 0, "total_corrections": 0}


@api_router.post("/inka-training/chat")
async def inka_training_chat(request: Request) -> Dict[str, Any]:
    """Interactive chat for training INKA"""
    try:
        body = await request.json()
        message = body.get("message", "")
        mode = body.get("mode", "learn")
        history = body.get("history", [])
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        _ensure_training_sheets()
        sheets_client = _get_inka_training_sheet()
        
        # Build context from training data
        training_context = ""
        learned = False
        
        if sheets_client:
            # Get existing knowledge
            knowledge = sheets_client.get_all_rows("INKA_Knowledge")
            scenarios = sheets_client.get_all_rows("INKA_Scenarios")
            corrections = sheets_client.get_all_rows("INKA_Corrections")
            
            # Add knowledge to context
            if len(knowledge) > 1:
                training_context += "\\n\\nИзученные знания:\\n"
                for row in knowledge[1:10]:  # Limit to recent 10
                    if len(row) >= 4:
                        training_context += f"- {row[2]}: {row[3][:100]}\\n"
            
            if len(scenarios) > 1:
                training_context += "\\n\\nИзученные сценарии:\\n"
                for row in scenarios[1:10]:
                    if len(row) >= 4:
                        training_context += f"- Вопрос: {row[2][:50]} -> Ответ: {row[3][:50]}\\n"
            
            if len(corrections) > 1:
                training_context += "\\n\\nКоррекции (чего избегать):\\n"
                for row in corrections[1:5]:
                    if len(row) >= 3:
                        training_context += f"- НЕ говорить: {row[1][:50]}, а говорить: {row[2][:50]}\\n"
        
        # Determine response based on mode
        if mode == "test":
            # In test mode, respond as if to a real client
            system_prompt = f"""Ты ИНКА - виртуальный ассистент тату-салона. 
Отвечай на вопрос клиента, используя свои знания.
{training_context}

Правила:
- Будь вежливой и профессиональной
- Давай конкретную информацию
- Предлагай записаться на консультацию"""
            
            response_text = await _generate_inka_response(message, system_prompt, history)
            
        else:
            # In learn mode, analyze admin's input for learning
            system_prompt = f"""Ты ИНКА в режиме обучения. Админ обучает тебя.
{training_context}

Твоя задача:
1. Понять что админ хочет тебе объяснить
2. Подтвердить понимание
3. Если это пример ответа - запомнить его
4. Если это исправление - принять к сведению
5. Если это вопрос - честно ответить

Формат ответа:
- Начни с понимания намерения
- Покажи что усвоила
- Попроси уточнения если нужно

Предыдущие сообщения: {history[-4:] if history else 'нет'}"""
            
            response_text = await _generate_inka_response(message, system_prompt, history)
            
            # Check if this is a learning opportunity
            learning_keywords = ['отвечай', 'говори', 'когда спрашивают', 'если клиент', 'запомни', 'важно', 'всегда', 'никогда']
            if any(kw in message.lower() for kw in learning_keywords):
                # Save this as a potential learning
                if sheets_client:
                    try:
                        session_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        sheets_client.service.spreadsheets().values().append(
                            spreadsheetId=sheets_client.spreadsheet_id,
                            range="INKA_Sessions!A:E",
                            valueInputOption="USER_ENTERED",
                            body={"values": [[
                                session_id,
                                "chat_learning",
                                message[:100],
                                response_text[:200],
                                datetime.now().isoformat()
                            ]]}
                        ).execute()
                        learned = True
                    except Exception as e:
                        logger.warning(f"Failed to save learning: {e}")
        
        return {"response": response_text, "learned": learned, "mode": mode}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in training chat: {e}")
        return {"response": f"Произошла ошибка: {str(e)}", "learned": False}


async def _generate_inka_response(message: str, system_prompt: str, history: list) -> str:
    """Generate INKA response using OpenAI"""
    try:
        import openai
        import os
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history
        for h in history[-6:]:  # Last 6 messages
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return f"Извините, не могу ответить сейчас. Ошибка: {str(e)}"


@api_router.post("/inka-training/scenario")
async def add_training_scenario(request: Request) -> Dict[str, Any]:
    """Add a training scenario"""
    try:
        body = await request.json()
        category = body.get("category", "general")
        trigger = body.get("trigger", "")
        response = body.get("response", "")
        context = body.get("context", "")
        
        if not trigger or not response:
            raise HTTPException(status_code=400, detail="Trigger and response are required")
        
        _ensure_training_sheets()
        sheets_client = _get_inka_training_sheet()
        
        if not sheets_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        scenario_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        sheets_client.service.spreadsheets().values().append(
            spreadsheetId=sheets_client.spreadsheet_id,
            range="INKA_Scenarios!A:F",
            valueInputOption="USER_ENTERED",
            body={"values": [[scenario_id, category, trigger, response, context, datetime.now().isoformat()]]}
        ).execute()
        
        return {"success": True, "id": scenario_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/scenarios")
async def get_training_scenarios() -> Dict[str, Any]:
    """Get all training scenarios"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            return {"scenarios": []}
        
        _ensure_training_sheets()
        data = sheets_client.get_all_rows("INKA_Scenarios")
        
        scenarios = []
        for row in data[1:]:  # Skip header
            if len(row) >= 4:
                scenarios.append({
                    "id": row[0],
                    "category": row[1],
                    "trigger": row[2],
                    "response": row[3],
                    "context": row[4] if len(row) > 4 else "",
                    "created_at": row[5] if len(row) > 5 else ""
                })
        
        return {"scenarios": scenarios}
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        return {"scenarios": []}


@api_router.delete("/inka-training/scenario/{scenario_id}")
async def delete_scenario(scenario_id: str) -> Dict[str, Any]:
    """Delete a training scenario"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        data = sheets_client.get_all_rows("INKA_Scenarios")
        
        for i, row in enumerate(data):
            if row and row[0] == scenario_id:
                # Delete row
                sheets_client.service.spreadsheets().batchUpdate(
                    spreadsheetId=sheets_client.spreadsheet_id,
                    body={
                        "requests": [{
                            "deleteDimension": {
                                "range": {
                                    "sheetId": _get_sheet_id(sheets_client, "INKA_Scenarios"),
                                    "dimension": "ROWS",
                                    "startIndex": i,
                                    "endIndex": i + 1
                                }
                            }
                        }]
                    }
                ).execute()
                return {"success": True}
        
        raise HTTPException(status_code=404, detail="Scenario not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/inka-training/correction")
async def add_correction(request: Request) -> Dict[str, Any]:
    """Add a correction"""
    try:
        body = await request.json()
        wrong_response = body.get("wrong_response", "")
        correct_response = body.get("correct_response", "")
        reason = body.get("reason", "")
        
        if not wrong_response or not correct_response:
            raise HTTPException(status_code=400, detail="Both responses are required")
        
        _ensure_training_sheets()
        sheets_client = _get_inka_training_sheet()
        
        if not sheets_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        correction_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        sheets_client.service.spreadsheets().values().append(
            spreadsheetId=sheets_client.spreadsheet_id,
            range="INKA_Corrections!A:E",
            valueInputOption="USER_ENTERED",
            body={"values": [[correction_id, wrong_response, correct_response, reason, datetime.now().isoformat()]]}
        ).execute()
        
        return {"success": True, "id": correction_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/corrections")
async def get_corrections() -> Dict[str, Any]:
    """Get all corrections"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            return {"corrections": []}
        
        _ensure_training_sheets()
        data = sheets_client.get_all_rows("INKA_Corrections")
        
        corrections = []
        for row in data[1:]:
            if len(row) >= 3:
                corrections.append({
                    "id": row[0],
                    "wrong_response": row[1],
                    "correct_response": row[2],
                    "reason": row[3] if len(row) > 3 else "",
                    "created_at": row[4] if len(row) > 4 else ""
                })
        
        return {"corrections": corrections}
    except Exception as e:
        logger.error(f"Error getting corrections: {e}")
        return {"corrections": []}


@api_router.delete("/inka-training/correction/{correction_id}")
async def delete_correction(correction_id: str) -> Dict[str, Any]:
    """Delete a correction"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        data = sheets_client.get_all_rows("INKA_Corrections")
        
        for i, row in enumerate(data):
            if row and row[0] == correction_id:
                sheets_client.service.spreadsheets().batchUpdate(
                    spreadsheetId=sheets_client.spreadsheet_id,
                    body={
                        "requests": [{
                            "deleteDimension": {
                                "range": {
                                    "sheetId": _get_sheet_id(sheets_client, "INKA_Corrections"),
                                    "dimension": "ROWS",
                                    "startIndex": i,
                                    "endIndex": i + 1
                                }
                            }
                        }]
                    }
                ).execute()
                return {"success": True}
        
        raise HTTPException(status_code=404, detail="Correction not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/inka-training/knowledge")
async def add_knowledge(request: Request) -> Dict[str, Any]:
    """Add knowledge to INKA"""
    try:
        body = await request.json()
        knowledge_type = body.get("type", "fact")
        title = body.get("title", "")
        content = body.get("content", "")
        
        if not title or not content:
            raise HTTPException(status_code=400, detail="Title and content are required")
        
        _ensure_training_sheets()
        sheets_client = _get_inka_training_sheet()
        
        if not sheets_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        knowledge_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        sheets_client.service.spreadsheets().values().append(
            spreadsheetId=sheets_client.spreadsheet_id,
            range="INKA_Knowledge!A:E",
            valueInputOption="USER_ENTERED",
            body={"values": [[knowledge_id, knowledge_type, title, content, datetime.now().isoformat()]]}
        ).execute()
        
        return {"success": True, "id": knowledge_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/knowledge")
async def get_knowledge() -> Dict[str, Any]:
    """Get all knowledge"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            return {"knowledge": []}
        
        _ensure_training_sheets()
        data = sheets_client.get_all_rows("INKA_Knowledge")
        
        knowledge = []
        for row in data[1:]:
            if len(row) >= 4:
                knowledge.append({
                    "id": row[0],
                    "type": row[1],
                    "title": row[2],
                    "content": row[3],
                    "created_at": row[4] if len(row) > 4 else ""
                })
        
        return {"knowledge": knowledge}
    except Exception as e:
        logger.error(f"Error getting knowledge: {e}")
        return {"knowledge": []}


@api_router.delete("/inka-training/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: str) -> Dict[str, Any]:
    """Delete knowledge entry"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        data = sheets_client.get_all_rows("INKA_Knowledge")
        
        for i, row in enumerate(data):
            if row and row[0] == knowledge_id:
                sheets_client.service.spreadsheets().batchUpdate(
                    spreadsheetId=sheets_client.spreadsheet_id,
                    body={
                        "requests": [{
                            "deleteDimension": {
                                "range": {
                                    "sheetId": _get_sheet_id(sheets_client, "INKA_Knowledge"),
                                    "dimension": "ROWS",
                                    "startIndex": i,
                                    "endIndex": i + 1
                                }
                            }
                        }]
                    }
                ).execute()
                return {"success": True}
        
        raise HTTPException(status_code=404, detail="Knowledge not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/recent")
async def get_recent_trainings() -> Dict[str, Any]:
    """Get recent training sessions"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            return {"recent": []}
        
        _ensure_training_sheets()
        data = sheets_client.get_all_rows("INKA_Sessions")
        
        recent = []
        for row in data[-11:-1]:  # Last 10
            if len(row) >= 3:
                recent.append({
                    "id": row[0],
                    "type": row[1],
                    "summary": row[2],
                    "timestamp": row[4] if len(row) > 4 else ""
                })
        
        return {"recent": recent[::-1]}  # Reverse to show newest first
    except Exception as e:
        logger.error(f"Error getting recent trainings: {e}")
        return {"recent": []}


@api_router.get("/inka-training/export")
async def export_training() -> Dict[str, Any]:
    """Export all training data"""
    try:
        sheets_client = _get_inka_training_sheet()
        if not sheets_client:
            return {"knowledge": [], "scenarios": [], "corrections": [], "sessions": []}
        
        _ensure_training_sheets()
        
        knowledge = sheets_client.get_all_rows("INKA_Knowledge")
        scenarios = sheets_client.get_all_rows("INKA_Scenarios")
        corrections = sheets_client.get_all_rows("INKA_Corrections")
        sessions = sheets_client.get_all_rows("INKA_Sessions")
        
        return {
            "export_date": datetime.now().isoformat(),
            "knowledge": knowledge[1:] if len(knowledge) > 1 else [],
            "scenarios": scenarios[1:] if len(scenarios) > 1 else [],
            "corrections": corrections[1:] if len(corrections) > 1 else [],
            "sessions": sessions[1:] if len(sessions) > 1 else []
        }
    except Exception as e:
        logger.error(f"Error exporting training: {e}")
        return {"error": str(e)}


@api_router.post("/inka-training/import")
async def import_training(request: Request) -> Dict[str, Any]:
    """Import training data"""
    try:
        body = await request.json()
        
        _ensure_training_sheets()
        sheets_client = _get_inka_training_sheet()
        
        if not sheets_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        imported = {"knowledge": 0, "scenarios": 0, "corrections": 0}
        
        # Import knowledge
        if "knowledge" in body and body["knowledge"]:
            for item in body["knowledge"]:
                if len(item) >= 4:
                    sheets_client.service.spreadsheets().values().append(
                        spreadsheetId=sheets_client.spreadsheet_id,
                        range="INKA_Knowledge!A:E",
                        valueInputOption="USER_ENTERED",
                        body={"values": [item[:5]]}
                    ).execute()
                    imported["knowledge"] += 1
        
        # Import scenarios
        if "scenarios" in body and body["scenarios"]:
            for item in body["scenarios"]:
                if len(item) >= 4:
                    sheets_client.service.spreadsheets().values().append(
                        spreadsheetId=sheets_client.spreadsheet_id,
                        range="INKA_Scenarios!A:F",
                        valueInputOption="USER_ENTERED",
                        body={"values": [item[:6]]}
                    ).execute()
                    imported["scenarios"] += 1
        
        # Import corrections
        if "corrections" in body and body["corrections"]:
            for item in body["corrections"]:
                if len(item) >= 3:
                    sheets_client.service.spreadsheets().values().append(
                        spreadsheetId=sheets_client.spreadsheet_id,
                        range="INKA_Corrections!A:E",
                        valueInputOption="USER_ENTERED",
                        body={"values": [item[:5]]}
                    ).execute()
                    imported["corrections"] += 1
        
        return {"success": True, "imported": imported}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_sheet_id(sheets_client, sheet_name: str) -> int:
    """Get sheet ID by name"""
    try:
        metadata = sheets_client.service.spreadsheets().get(
            spreadsheetId=sheets_client.spreadsheet_id
        ).execute()
        
        for sheet in metadata.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        return 0
    except:
        return 0


# ================== BEHAVIOR ANALYSIS ==================

@api_router.post("/behavior/analyze")
async def analyze_behavior(request: Request) -> Dict[str, Any]:
    """Анализировать поведение по тексту сообщения"""
    try:
        from src.services.behavior_service import get_behavior_service
        
        body = await request.json()
        text = body.get("text", "")
        context = body.get("context", [])
        tg_id = body.get("tg_id")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        behavior_service = get_behavior_service()
        result = behavior_service.analyze_message_behavior(text, context)
        
        # Если указан tg_id - сохраняем в историю
        if tg_id:
            behavior_service.add_message_to_history(str(tg_id), text, result)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing behavior: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/behavior/client/{tg_id}")
async def get_client_behavior(tg_id: str) -> Dict[str, Any]:
    """Получить информацию о поведении клиента"""
    try:
        from src.services.behavior_service import get_behavior_service
        
        behavior_service = get_behavior_service()
        
        return {
            "tg_id": tg_id,
            "risk_level": behavior_service.calculate_risk_level(tg_id),
            "access": behavior_service.get_access_info(tg_id),
            "message_history_count": len(behavior_service.get_message_history(tg_id))
        }
    except Exception as e:
        logger.error(f"Error getting client behavior: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/behavior/event")
async def record_behavior_event(request: Request) -> Dict[str, Any]:
    """Записать событие поведения (визит, отмена, неявка и т.д.)"""
    try:
        from src.services.behavior_service import get_behavior_service
        
        body = await request.json()
        tg_id = body.get("tg_id")
        event_type = body.get("event_type")
        
        if not tg_id or not event_type:
            raise HTTPException(status_code=400, detail="tg_id and event_type are required")
        
        behavior_service = get_behavior_service()
        new_risk = behavior_service.record_event(str(tg_id), event_type)
        
        return {
            "success": True,
            "tg_id": tg_id,
            "event_type": event_type,
            "new_risk_level": new_risk
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording behavior event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/behavior/check-booking/{tg_id}")
async def check_booking_allowed(tg_id: str) -> Dict[str, Any]:
    """Проверить, разрешена ли запись клиенту"""
    try:
        from src.services.behavior_service import get_behavior_service
        
        behavior_service = get_behavior_service()
        allowed, reason = behavior_service.is_booking_allowed(tg_id)
        
        return {
            "tg_id": tg_id,
            "allowed": allowed,
            "reason": reason,
            "access": behavior_service.get_access_info(tg_id)
        }
    except Exception as e:
        logger.error(f"Error checking booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/behavior/types")
async def get_behavior_types() -> Dict[str, Any]:
    """Получить список типов поведения и уровней риска"""
    from src.services.behavior_service import BEHAVIOR_TYPES, ACCESS_LEVELS, BEHAVIOR_EVENTS
    
    return {
        "behavior_types": BEHAVIOR_TYPES,
        "access_levels": ACCESS_LEVELS,
        "behavior_events": BEHAVIOR_EVENTS
    }


# ================== ADMINS MANAGEMENT ==================

@api_router.get("/admins")
async def get_admins() -> List[Dict[str, Any]]:
    """Get all admin users"""
    try:
        from src.web.auth import get_admin_users
        
        admins = get_admin_users()
        # Don't return password hashes
        safe_admins = []
        for admin in admins:
            safe_admin = {
                "id": admin.get("id"),
                "username": admin.get("username"),
                "role": admin.get("role", "admin"),
                "created_at": admin.get("created_at"),
                "last_login": admin.get("last_login"),
                "telegram_id": admin.get("telegram_id"),
                "is_active": admin.get("is_active", True)
            }
            safe_admins.append(safe_admin)
        return safe_admins
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        raise HTTPException(status_code=500, detail="Error getting admins")


@api_router.post("/admins")
async def create_admin(request: Request) -> Dict[str, Any]:
    """Create new admin user"""
    try:
        from src.web.auth import add_admin_user
        
        body = await request.json()
        
        # Validate required fields
        username = body.get("username", "").strip()
        password = body.get("password", "")
        
        if not username:
            raise HTTPException(status_code=400, detail="Username is required")
        if not password or len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        success, message = add_admin_user(
            username=username,
            password=password,
            role=body.get("role", "admin"),
            telegram_id=body.get("telegram_id")
        )
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating admin: {e}")
        raise HTTPException(status_code=500, detail="Error creating admin")


@api_router.put("/admins/{admin_id}")
async def update_admin(admin_id: str, request: Request) -> Dict[str, Any]:
    """Update admin user"""
    try:
        from src.web.auth import update_admin_user
        
        body = await request.json()
        
        success, message = update_admin_user(admin_id, body)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating admin: {e}")
        raise HTTPException(status_code=500, detail="Error updating admin")


@api_router.delete("/admins/{admin_id}")
async def delete_admin(admin_id: str) -> Dict[str, Any]:
    """Delete admin user"""
    try:
        from src.web.auth import delete_admin_user
        
        success, message = delete_admin_user(admin_id)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting admin: {e}")
        raise HTTPException(status_code=500, detail="Error deleting admin")


@api_router.post("/admins/{admin_id}/change-password")
async def change_admin_password(admin_id: str, request: Request) -> Dict[str, Any]:
    """Change admin password"""
    try:
        from src.web.auth import change_admin_password as do_change_password
        
        body = await request.json()
        
        new_password = body.get("new_password", "")
        current_password = body.get("current_password", "")
        
        if not new_password or len(new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        
        success, message = do_change_password(admin_id, new_password, current_password)
        
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail="Error changing password")


@api_router.put("/admins/{admin_id}/toggle-status")
async def toggle_admin_status(admin_id: str) -> Dict[str, Any]:
    """Toggle admin active status"""
    try:
        from src.web.auth import toggle_admin_status as do_toggle
        
        success, message, is_active = do_toggle(admin_id)
        
        if success:
            return {"success": True, "message": message, "is_active": is_active}
        else:
            raise HTTPException(status_code=400, detail=message)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling admin status: {e}")
        raise HTTPException(status_code=500, detail="Error toggling admin status")


# ================== HEALTH ==================

@api_router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "service": "tattoo-bot-admin", "timestamp": datetime.now().isoformat()}
