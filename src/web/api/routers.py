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
    """Get all bookings with optional filters"""
    try:
        from src.web.app import db_manager
        
        if not db_manager:
            raise HTTPException(status_code=500, detail="Database manager not initialized")
        
        bookings = db_manager.get_all_bookings()
        
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


# ================== HEALTH ==================

@api_router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "service": "tattoo-bot-admin", "timestamp": datetime.now().isoformat()}
