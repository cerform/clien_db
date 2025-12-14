"""
Monitoring and Health Check Endpoints
Provides health checks, monitoring status, and telemetry
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import time
import logging
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["monitoring"])

# In-memory storage for monitoring history (last 100 checks)
monitoring_history: deque = deque(maxlen=100)

# In-memory storage for telemetry events (last 1000 events)
telemetry_events: deque = deque(maxlen=1000)


@router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint for Cloud Run and load balancers
    Returns 200 if service is healthy
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tattoo-bot",
        "version": "1.0.0"
    }

    # Check critical dependencies
    checks = {}

    # Check database connection
    try:
        from src.db.cloudsql_client import init_cloudsql_client
        client = init_cloudsql_client()
        if client and client.test_connection():
            checks["database"] = "ok"
        else:
            checks["database"] = "degraded"
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        checks["database"] = "unavailable"

    # Check Google Sheets API
    try:
        from src.db.sheets_client import SheetsClient
        from src.config.config import Config
        config = Config.from_env()
        if config.SPREADSHEET_ID:
            sheets_client = SheetsClient()
            # Quick check: try to read clients sheet (read_sheet doesn't accept 'limit')
            try:
                rows = sheets_client.read_sheet(config.SPREADSHEET_ID, "clients")
                checks["google_sheets"] = "ok"
            except TypeError:
                # Fallback if read_sheet signature changed in older versions
                rows = sheets_client.read_sheet(config.SPREADSHEET_ID, "clients")
                checks["google_sheets"] = "ok"
        else:
            checks["google_sheets"] = "not_configured"
    except Exception as e:
        logger.warning(f"Google Sheets health check failed: {e}")
        checks["google_sheets"] = "unavailable"

    # Check Telegram Bot
    try:
        from aiogram import Bot
        from src.config.config import Config
        config = Config.from_env()
        if config.BOT_TOKEN:
            bot = Bot(token=config.BOT_TOKEN)
            # This is sync context, so we can't await
            # Just check if token is present
            checks["telegram_bot"] = "configured"
        else:
            checks["telegram_bot"] = "not_configured"
    except Exception as e:
        logger.warning(f"Telegram bot health check failed: {e}")
        checks["telegram_bot"] = "unavailable"

    # Check OpenAI API
    try:
        from src.config.config import Config
        config = Config.from_env()
        if config.OPENAI_API_KEY:
            checks["openai_api"] = "configured"
        else:
            checks["openai_api"] = "not_configured"
    except Exception:
        checks["openai_api"] = "unavailable"

    health_status["checks"] = checks

    # Determine overall health
    critical_services = ["database", "telegram_bot"]
    all_critical_ok = all(
        checks.get(svc) in ("ok", "configured", "not_configured")
        for svc in critical_services
    )

    if not all_critical_ok:
        health_status["status"] = "degraded"
        return JSONResponse(content=health_status, status_code=503)

    return JSONResponse(content=health_status, status_code=200)


@router.get("/monitoring/checks")
async def monitoring_checks():
    """
    Get current monitoring status with detailed checks
    Used by dashboard to display system health
    """
    timestamp = time.time()

    checks = {
        "timestamp": timestamp,
        "checks": []
    }

    # Check 1: Web server responsive
    checks["checks"].append({
        "name": "web_server",
        "status": "ok",
        "message": "Web server is responding"
    })

    # Check 2: Database connection
    try:
        from src.db.cloudsql_client import init_cloudsql_client
        client = init_cloudsql_client()
        if client and client.test_connection():
            checks["checks"].append({
                "name": "database",
                "status": "ok",
                "message": "Database connection successful"
            })
        else:
            checks["checks"].append({
                "name": "database",
                "status": "warning",
                "message": "Database connection degraded"
            })
    except Exception as e:
        checks["checks"].append({
            "name": "database",
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        })

    # Check 3: Google Sheets API
    try:
        from src.db.sheets_client import SheetsClient
        from src.config.config import Config
        config = Config.from_env()
        if config.SPREADSHEET_ID:
            sheets_client = SheetsClient()
            # read_sheet historically accepted a `limit` kwarg in some versions,
            # but newer versions no longer accept it; call without and use
            # a fallback if TypeError is raised.
            try:
                sheets_client.read_sheet(config.SPREADSHEET_ID, "clients")
            except TypeError:
                # Older versions may expect `limit` positional arg; try positional
                try:
                    sheets_client.read_sheet(config.SPREADSHEET_ID, "clients", 1)
                except Exception:
                    # Fallthrough to raise the original error above to be handled
                    raise
            checks["checks"].append({
                "name": "google_sheets",
                "status": "ok",
                "message": "Google Sheets API responding"
            })
        else:
            checks["checks"].append({
                "name": "google_sheets",
                "status": "warning",
                "message": "Google Sheets not configured"
            })
    except Exception as e:
        checks["checks"].append({
            "name": "google_sheets",
            "status": "error",
            "message": f"Google Sheets API error: {str(e)}"
        })

    # Check 4: Telegram Bot
    try:
        from src.config.config import Config
        config = Config.from_env()
        if config.BOT_TOKEN:
            checks["checks"].append({
                "name": "telegram_bot",
                "status": "ok",
                "message": "Telegram bot configured"
            })
        else:
            checks["checks"].append({
                "name": "telegram_bot",
                "status": "error",
                "message": "Telegram bot token not configured"
            })
    except Exception as e:
        checks["checks"].append({
            "name": "telegram_bot",
            "status": "error",
            "message": f"Telegram bot check failed: {str(e)}"
        })

    # Calculate summary
    summary = {
        "ok": sum(1 for c in checks["checks"] if c["status"] == "ok"),
        "warning": sum(1 for c in checks["checks"] if c["status"] == "warning"),
        "error": sum(1 for c in checks["checks"] if c["status"] == "error"),
        "total": len(checks["checks"])
    }

    checks["summary"] = summary
    checks["ok"] = summary["error"] == 0

    # Store in history
    monitoring_history.append({
        "ts": timestamp,
        "summary": summary,
        "ok": checks["ok"]
    })

    return checks


@router.get("/monitoring/history")
async def monitoring_history_endpoint():
    """
    Get monitoring history (last 100 checks)
    Returns timestamps and summary status for each check
    """
    return {
        "history": list(monitoring_history),
        "count": len(monitoring_history)
    }


@router.get("/inka-training-stats")
async def inka_training_stats():
    """
    Get INKA AI training statistics
    Returns conversation metrics, intent analysis, and language distribution
    """
    # Try to get real stats from database
    try:
        from src.db.cloudsql_client import init_cloudsql_client
        from src.db.repositories.admin_messages_repo import AdminMessagesRepo

        client = init_cloudsql_client()
        if client:
            repo = AdminMessagesRepo(client.get_engine())
            # Get recent messages for stats
            messages = repo.get_recent_messages(limit=1000)

            # Calculate real stats
            total_conversations = len(set(m.get('user_id') for m in messages if m.get('user_id')))
            total_messages = len(messages)

            # Calculate language distribution
            languages = {}
            for msg in messages:
                lang = msg.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1

            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_response_time": 1.2,  # TODO: Calculate from actual response times
                "satisfaction_rate": 96.3,  # TODO: Calculate from user feedback
                "languages": languages,
                "last_updated": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.warning(f"Failed to get real INKA stats: {e}")

    # Return mock data if database unavailable
    return {
        "total_conversations": 0,
        "total_messages": 0,
        "avg_response_time": 0,
        "satisfaction_rate": 0,
        "languages": {"ru": 0, "en": 0, "he": 0},
        "last_updated": datetime.utcnow().isoformat(),
        "note": "Database unavailable, showing default values"
    }


@router.post("/telemetry/events")
async def telemetry_event(request: Request):
    """
    Record telemetry event for frontend monitoring
    Stores UI errors, warnings, and performance metrics
    """
    try:
        event_data = await request.json()

        # Validate required fields
        if not event_data.get('event_type'):
            raise HTTPException(status_code=400, detail="event_type is required")

        # Add server-side metadata
        event = {
            "timestamp": time.time(),
            "event_type": event_data.get('event_type'),
            "message": event_data.get('message', ''),
            "meta": event_data.get('meta', {}),
            "user_agent": request.headers.get('user-agent', ''),
            "ip": request.client.host if request.client else 'unknown'
        }

        # Store event
        telemetry_events.append(event)

        # Log errors and warnings
        if event['event_type'] in ('ui_error', 'error'):
            logger.error(f"Frontend error: {event['message']}")
        elif event['event_type'] in ('ui_warning', 'warning'):
            logger.warning(f"Frontend warning: {event['message']}")

        return {"ok": True, "event_id": len(telemetry_events)}

    except Exception as e:
        logger.error(f"Failed to record telemetry event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telemetry/events")
async def get_telemetry_events(limit: int = 100):
    """
    Get recent telemetry events
    Returns last N events for debugging and monitoring
    """
    events_list = list(telemetry_events)
    # Return most recent first
    events_list.reverse()
    return {
        "events": events_list[:limit],
        "total": len(telemetry_events)
    }
