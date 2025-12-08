"""API routers for web interface"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api", tags=["api"])


@api_router.get('/monitoring/checks')
async def monitoring_checks() -> Dict[str, Any]:
    """Run quick health checks for important endpoints and return the summary"""
    from fastapi.testclient import TestClient
    from src.web.app import create_app

    app = create_app()
    client = TestClient(app)
    endpoints = [
        ('health', '/api/health'),
        ('stats', '/api/stats'),
        ('masters', '/api/masters'),
        ('clients', '/api/clients'),
        ('inka_stats', '/api/inka-training/stats')
    ]
    results = {}
    for name, url in endpoints:
        try:
            r = client.get(url)
            results[name] = { 'status': r.status_code, 'ok': r.status_code == 200 }
        except Exception as e:
            results[name] = { 'status': 'error', 'error': str(e) }
    return { 'ok': all(v.get('ok', False) for v in results.values()), 'results': results }

# ================== CLIENTS ==================

@api_router.get("/clients")
async def get_clients() -> List[dict]:
    from src.web.app import db_manager
    if db_manager is None:
        logger.error("Database manager not initialized")
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db_manager.get_all_clients()
    except Exception as e:
        logger.error(f"Error getting clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/clients")
async def create_client(request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        data = await request.json()
        success, message = db_manager.add_client(data)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/clients/{client_id}")
async def update_client(client_id: str, request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        data = await request.json()
        success, message = db_manager.edit_client(client_id, data)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error updating client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        success, message = db_manager.delete_client(client_id)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error deleting client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================== MASTERS ==================

@api_router.get("/masters")
async def get_masters() -> List[dict]:
    from src.web.app import db_manager
    if db_manager is None:
        logger.error("Database manager not initialized")
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db_manager.get_all_masters()
    except Exception as e:
        logger.error(f"Error getting masters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/masters")
async def create_master(request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        data = await request.json()
        success, message = db_manager.add_master(data)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error creating master: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/masters/{master_id}")
async def update_master(master_id: str, request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        data = await request.json()
        success, message = db_manager.edit_master(master_id, data)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error updating master: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/masters/{master_id}")
async def delete_master(master_id: str) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        success, message = db_manager.delete_master(master_id)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error deleting master: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================== SERVICES ==================

@api_router.get("/services")
async def get_services() -> List[dict]:
    from src.web.app import db_manager
    if db_manager is None:
        logger.error("Database manager not initialized")
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db_manager.get_all_services()
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/services")
async def create_service(request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        data = await request.json()
        success, message = db_manager.add_service(data)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error creating service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/services/{service_id}")
async def update_service(service_id: str, request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        data = await request.json()
        success, message = db_manager.edit_service(service_id, data)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error updating service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        success, message = db_manager.delete_service(service_id)
        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=400, detail=message)
    except Exception as e:
        logger.error(f"Error deleting service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================== BOOKINGS ==================

@api_router.get("/bookings")
async def get_bookings() -> List[dict]:
    from src.web.app import db_manager
    if db_manager is None:
        logger.error("Database manager not initialized")
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db_manager.get_all_bookings()
    except Exception as e:
        logger.error(f"Error getting bookings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== STATISTICS ==================

@api_router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    try:
        from src.web.app import db_manager
        
        if db_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        clients = db_manager.get_all_clients()
        masters = db_manager.get_all_masters()
        services = db_manager.get_all_services()
        bookings = db_manager.get_all_bookings()
        
        active_bookings = [b for b in bookings if b.get("status") in ["pending", "confirmed"]]
        completed_bookings = [b for b in bookings if b.get("status") == "completed"]
        
        total_revenue = sum(float(b.get("price", 0) or 0) for b in completed_bookings)
        
        return {
            "clients_count": len(clients),
            "masters_count": len(masters),
            "services_count": len(services),
            "bookings_count": len(bookings),
            "active_bookings": len(active_bookings),
            "completed_bookings": len(completed_bookings),
            "total_revenue": total_revenue,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


# ================== SHEETS / DB MANAGEMENT ==================


@api_router.get("/sheets")
async def list_sheets() -> List[str]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db_manager.list_sheets()
    except Exception as e:
        logger.error(f"Error listing sheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/sheets/{sheet_name}")
async def export_sheet(sheet_name: str) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db_manager.export_sheet(sheet_name)
    except Exception as e:
        logger.error(f"Error exporting sheet {sheet_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/sheets/{sheet_name}/import")
async def import_sheet(sheet_name: str, request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        body = await request.json()
        rows = body.get('rows', [])
        mode = body.get('mode', 'append')
        success, msg = db_manager.import_sheet(sheet_name, rows, mode=mode)
        if success:
            # audit
            admin_id = body.get('admin_id')
            try:
                if admin_id:
                    db_manager.add_audit_log(admin_id, 'import_sheet', sheet_name, f'imported:{len(rows)} mode={mode}')
            except:
                pass
            return {"success": True, "message": msg}
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logger.error(f"Error importing sheet {sheet_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/db/backup")
async def backup_db() -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        data = db_manager.backup_db()
        # We don't get admin info here, but still store a brief log
        try:
            db_manager.add_audit_log('web', 'backup_db', 'ALL', 'backup created')
        except:
            pass
        return data
    except Exception as e:
        logger.error(f"Error backing up DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/db/restore")
async def restore_db(request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        body = await request.json()
        data = body.get('backup', {})
        mode = body.get('mode', 'replace')
        success, msg = db_manager.restore_db(data, mode=mode)
        if success:
            admin_id = body.get('admin_id')
            try:
                if admin_id:
                    db_manager.add_audit_log(admin_id, 'restore_db', 'ALL', f'restore mode={mode}')
            except:
                pass
            return {"success": True, "message": msg}
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logger.error(f"Error restoring DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get('/audit/logs')
async def get_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        return db_manager.get_audit_logs(limit=limit)
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post('/audit/logs')
async def add_audit_log(request: Request) -> Dict[str, Any]:
    from src.web.app import db_manager
    if db_manager is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    try:
        body = await request.json()
        admin_id = body.get('admin_id')
        action = body.get('action', '')
        sheet = body.get('sheet', '')
        details = body.get('details', '')
        success = db_manager.add_audit_log(admin_id or 'web', action, sheet, details)
        if success:
            return {"success": True}
        raise HTTPException(status_code=500, detail='Failed to add audit log')
    except Exception as e:
        logger.error(f"Error adding audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== INKA TRAINING ==================

@api_router.get("/inka-training-stats")
async def get_inka_training_stats() -> Dict[str, Any]:
    try:
        from src.web.app import learning_system
        if learning_system is None:
            # provide fallback default when learning system is not initialized
            return {
                "total_sessions": 0,
                "successful_trainings": 0,
                "average_score": 0
            }
        # If a learning_system object exists, we can query it for stats (placeholder)
        return {
            "total_sessions": getattr(learning_system, 'total_sessions', 0),
            "successful_trainings": getattr(learning_system, 'successful_trainings', 0),
            "average_score": getattr(learning_system, 'average_score', 0)
        }
    except Exception as e:
        logger.error(f"Error getting INKA stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/stats")
async def get_inka_training_stats_alt() -> Dict[str, Any]:
    return await get_inka_training_stats()


@api_router.post("/inka-training/chat")
async def inka_chat(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        message = body.get('message', '')
        return {"response": f"Echo: {message}" if message else "", "learned": False}
    except Exception as e:
        logger.error(f"Error INKA chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/inka-training/scenario")
async def create_scenario(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return {"success": True, "message": "Scenario created"}
    except Exception as e:
        logger.error(f"Error creating scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/scenarios")
async def get_scenarios() -> Dict[str, Any]:
    try:
        return {"scenarios": []}
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/inka-training/correction")
async def create_correction(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error creating correction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/corrections")
async def get_corrections() -> Dict[str, Any]:
    try:
        return {"corrections": []}
    except Exception as e:
        logger.error(f"Error getting corrections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/inka-training/knowledge")
async def create_knowledge(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error creating knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/knowledge")
async def get_knowledge() -> Dict[str, Any]:
    try:
        return {"knowledge": []}
    except Exception as e:
        logger.error(f"Error getting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/inka-training/recent")
async def get_recent_trainings() -> Dict[str, Any]:
    try:
        return {"recent": []}
    except Exception as e:
        logger.error(f"Error getting recent inka trainings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/inka-training/export")
async def export_training_data() -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error exporting inka data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/inka-training/import")
async def import_training_data(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return {"success": True, "imported": len(body.get('entries', [])) if isinstance(body, dict) else 0}
    except Exception as e:
        logger.error(f"Error importing inka data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/inka-training/scenario/{id}")
async def remove_scenario(id: str) -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting scenario {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/inka-training/correction/{id}")
async def remove_correction(id: str) -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting correction {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/inka-training/knowledge/{id}")
async def remove_knowledge(id: str) -> Dict[str, Any]:
    try:
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting knowledge {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ================== CALENDAR SYNC ==================

@api_router.post("/calendar/sync/{master_id}")
async def sync_calendar_to_schedule(master_id: str, request: Request) -> Dict[str, Any]:
    try:
        from src.web.app import db_manager
        from src.config import config
        from src.calendars.google_calendar_sync import GoogleCalendarSync
        
        if db_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        body = await request.json()
        action = body.get("action", "preview")
        
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        calendar_id = master.get("calendar_id")
        calendar = GoogleCalendarSync(
            getattr(config, 'google_credentials_file', 'credentials.json'),
            calendar_id
        )
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        events = calendar.get_events(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        ) or []
        
        day_names = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        working_days = {}

        for event in events:
            event_start = event.get("start", {}).get("dateTime")
            event_end = event.get("end", {}).get("dateTime")
            if not event_start:
                continue

            start_dt = datetime.fromisoformat(event_start.replace("Z","+00:00"))
            end_dt = datetime.fromisoformat(event_end.replace("Z","+00:00")) if event_end else start_dt + timedelta(hours=8)

            day_name = day_names[start_dt.weekday()]
            working_days[day_name] = {
                "start": start_dt.strftime("%H:%M"),
                "end": end_dt.strftime("%H:%M"),
                "is_working": "TRUE"
            }

        schedule_data = db_manager.get_schedule(master_id).get("schedule", [])

        if action == "preview":
            return {
                "success": True,
                "working_days": working_days,
                "current_schedule": schedule_data
            }

        if action == "sync_to_db":
            updated = 0
            created = 0

            for day_name, hours in working_days.items():
                existing = next((s for s in schedule_data if s.get("day_of_week") == day_name), None)

                if existing:
                    db_manager.update_schedule_entry(existing["id"], {
                        "start_time": hours["start"],
                        "end_time": hours["end"],
                        "is_working": "TRUE"
                    })
                    updated += 1
                else:
                    new_entry = {
                        "id": str(uuid.uuid4()),
                        "master_id": master_id,
                        "day_of_week": day_name,
                        "start_time": hours["start"],
                        "end_time": hours["end"],
                        "is_working": "TRUE"
                    }
                    db_manager.add_schedule_entry(new_entry)
                    created += 1

            return {
                "success": True,
                "updated": updated,
                "created": created
            }

        raise HTTPException(status_code=400, detail="Unknown action")

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))


# ================== AVAILABILITY ==================

@api_router.get("/calendar/availability/{master_id}")
async def get_master_availability(master_id: str, date: str) -> Dict[str, Any]:
    try:
        from src.web.app import db_manager
        
        if db_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Define all available time slots
        all_slots = [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in range(0, 60, 30)]
        busy_slots = set()
        
        bookings = db_manager.get_all_bookings()
        for booking in bookings:
            if booking.get("master_id") == master_id and booking.get("date") == date:
                if booking.get("status") not in ["cancelled"]:
                    time = booking.get("time", "")
                    if time:
                        busy_slots.add(time[:5] if len(time) > 5 else time)
        
        available_slots = [slot for slot in all_slots if slot not in busy_slots]
        
        return {
            "available_slots": available_slots,
            "busy_slots": list(busy_slots)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ================== MASTER CALENDAR VIEW ==================

@api_router.get("/calendar/master/{master_id}")
async def get_master_calendar(master_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Get master's calendar with events and free slots"""
    try:
        from src.web.app import db_manager
        from src.calendars.google_calendar_sync import GoogleCalendarSync
        from src.config import config
        
        if db_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        # Get schedule for the week
        schedule = db_manager.get_schedule(master_id).get("schedule", [])
        
        # Get bookings for the date range
        bookings = db_manager.get_all_bookings()
        master_bookings = [b for b in bookings if b.get("master_id") == master_id 
                          and start_date <= b.get("date", "") <= end_date]
        
        # Get calendar events if calendar_id exists
        calendar_events = []
        if master.get("calendar_id"):
            try:
                calendar = GoogleCalendarSync(
                    getattr(config, 'google_credentials_file', 'credentials.json'),
                    master.get("calendar_id")
                )
                calendar_events = calendar.get_events(start_date, end_date) or []
            except Exception as e:
                logger.warning(f"Failed to load calendar events: {e}")
        
        return {
            "success": True,
            "master_id": master_id,
            "master_name": master.get("name", ""),
            "calendar_id": master.get("calendar_id", ""),
            "schedule": schedule,
            "bookings": master_bookings,
            "calendar_events": calendar_events
        }
    except Exception as e:
        logger.error(f"Error getting master calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/calendar/sync/{master_id}")
async def get_sync_status(master_id: str) -> Dict[str, Any]:
    """Get synchronization status for a master"""
    try:
        from src.web.app import db_manager
        
        if db_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        masters = db_manager.get_all_masters()
        master = next((m for m in masters if m.get("id") == master_id), None)
        if not master:
            raise HTTPException(status_code=404, detail="Master not found")
        
        calendar_id = master.get("calendar_id", "")
        schedule = db_manager.get_schedule(master_id).get("schedule", [])
        
        # Count calendar events from last 7 days
        from datetime import datetime, timedelta
        today = datetime.now()
        past_week = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        calendar_events = 0
        if calendar_id:
            try:
                from src.calendars.google_calendar_sync import GoogleCalendarSync
                from src.config import config
                
                calendar = GoogleCalendarSync(
                    getattr(config, 'google_credentials_file', 'credentials.json'),
                    calendar_id
                )
                events = calendar.get_events(past_week, today_str) or []
                calendar_events = len(events)
            except Exception as e:
                logger.error(f"Error getting calendar events: {e}")
                calendar_events = 0
        
        # Get bookings for this master
        bookings = db_manager.get_all_bookings()
        master_bookings = [b for b in bookings if b.get("master_id") == master_id]
        
        return {
            "status": "synced",
            "master_id": master_id,
            "calendar_id": calendar_id,
            "calendar_connected": bool(calendar_id),
            "calendar_events": calendar_events,
            "db_schedule_entries": len(schedule),
            "db_bookings": len(master_bookings),
            "scheduled_events": len(schedule),
            "schedule": schedule,
            "last_sync": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
