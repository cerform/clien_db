"""API routers for web interface"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

api_router = APIRouter(prefix="/api", tags=["api"])


# ================== STATISTICS ==================

@api_router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    try:
        from src.web.app import db_manager
        
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


# ================== CALENDAR SYNC ==================

@api_router.post("/calendar/sync/{master_id}")
async def sync_calendar_to_schedule(master_id: str, request: Request) -> Dict[str, Any]:
    try:
        from src.web.app import db_manager
        from src.config import config
        from src.calendars.google_calendar_sync import GoogleCalendarSync
        
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
        
        bookings = db_manager.get_all_bookings()
        for booking in bookings:
            if booking.get("master_id") == master_id and booking.get("date") == date:
                if booking.get("status") not in ["cancelled"]:
                    time = booking.get("time", "")
                    if time:
                        busy_slots.add(time[:5] if len(time) > 5 else time)
        
        available_slots = [slot for slot in all_slots if slot not in busy_slots]
        
        return {
            "available_slots": available,
            "busy_slots": busy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
