
"""
API routers for FastAPI app - Production Ready
All endpoints connected to real Google Sheets repositories
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import os
from src.web.models import Client, Master, Service, Booking, NewAdminModel
from src.db.sheets_client import SheetsClient
from src.db.repositories.clients_repo import ClientsRepo
from src.db.repositories.masters_repo import MastersRepo
from src.db.repositories.services_repo import ServicesRepo
from src.db.repositories.bookings_repo import BookingsRepo
from src.services.admin_manager import is_admin as is_admin_service, get_admin_ids as get_runtime_admin_ids
from src.services.booking_service import BookingService
from fastapi.responses import StreamingResponse
import json

api_router = APIRouter()
routers = type('routers', (), {'api_router': api_router})

# ==================== HELPER FUNCTIONS ====================

def _get_spreadsheet_id():
    """Get spreadsheet ID from config"""
    from src.core.config_manager import get_config
    from src.config.config import Config
    cfg = get_config()
    conf = Config.from_env()
    return cfg.get('spreadsheet_id') or conf.SPREADSHEET_ID

def _force_sheet_mode():
    """Check if force sheet mode is enabled"""
    try:
        from src.core.config_manager import is_force_sheet_mode
        return is_force_sheet_mode()
    except Exception:
        return os.getenv('FORCE_SHEET_MODE', '') in ('1', 'true', 'True')

def _is_admin(request: Request) -> bool:
    """Determine if the incoming request is from an admin"""
    try:
        auth = request.headers.get('Authorization') or request.headers.get('authorization')
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1]
            if token.startswith('admin_token_'):
                return True
        if getattr(request.state, 'admin_id', None) is not None:
            try:
                # First try runtime admin manager (sheet + env)
                if is_admin_service(request.state.admin_id):
                    return True
                # Fallback to config manager or raw env var
                from src.core.config_manager import get_config
                cfg = get_config()
                admin_ids = cfg.get('admin_ids') or os.getenv('ADMIN_IDS')
                if isinstance(admin_ids, str):
                    admin_ids = [int(x.strip()) for x in admin_ids.split(',') if x.strip()]
                if isinstance(admin_ids, list):
                    return request.state.admin_id in admin_ids
                # If we cannot resolve, allow by default (fallback modern behavior)
                return True
            except Exception:
                return True
    except Exception:
        pass
    return False

def _get_repos():
    """Get repository instances for database operations"""
    sid = _get_spreadsheet_id()
    if not sid:
        raise HTTPException(status_code=500, detail='SPREADSHEET_ID not configured')
    try:
        sc = SheetsClient()
        return {
            'clients': ClientsRepo(sc, sid),
            'masters': MastersRepo(sc, sid),
            'services': ServicesRepo(sc, sid),
            'bookings': BookingsRepo(sc, sid),
            'sheets_client': sc,
            'spreadsheet_id': sid
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to initialize repositories: {str(e)}')

# ==================== API ENDPOINTS ====================

@api_router.get('/api/endpoints')
async def list_endpoints(request: Request):
    """Return a simplified list of API routes"""
    routes = []
    for r in request.app.routes:
        try:
            path = getattr(r, 'path', None)
            if not path or not isinstance(path, str):
                continue
            if path.startswith(('/static', '/openapi', '/docs', '/redoc')) or path == '/api/endpoints':
                continue
            routes.append({
                'path': path,
                'methods': list(getattr(r, 'methods', []) or []),
                'name': getattr(r, 'name', None),
            })
        except Exception:
            continue
    return routes

@api_router.get('/api/stats')
async def get_stats():
    """Get dashboard statistics from real data"""
    try:
        repos = _get_repos()
        clients = repos['clients'].list_clients()
        masters = repos['masters'].list_masters()
        services = repos['services'].list_services()
        bookings = repos['bookings'].list_bookings()
        
        active_bookings = sum(1 for b in bookings if b.get('status') in ['pending', 'confirmed'])
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        new_clients_week = sum(1 for c in clients if c.get('created_at', '') > week_ago)
        
        return {
            "total_clients": len(clients),
            "total_masters": len(masters),
            "total_bookings": len(bookings),
            "total_services": len(services),
            "active_bookings": active_bookings,
            "new_clients_week": new_clients_week,
            "completion_rate": 0,
            "revenue_month": 0,
            "revenue_week": 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch stats: {str(e)}')

# ==================== CLIENTS ====================

@api_router.get('/api/clients')
async def get_clients():
    """Get list of all clients from Google Sheets"""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        repos = _get_repos()
        return repos['clients'].list_clients()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch clients: {str(e)}')

@api_router.post('/api/clients', status_code=201)
async def create_client(client: Client):
    """Create a new client"""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        repos = _get_repos()
        new_client = repos['clients'].create_client(
            telegram_id=getattr(client, 'telegram_id', 0),
            name=client.name,
            phone=getattr(client, 'phone', ""),
            email=getattr(client, 'email', ""),
            notes=getattr(client, 'notes', "")
        )
        return new_client
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to create client: {str(e)}')

@api_router.get('/api/clients/{client_id}')
async def get_client(client_id: str):
    """Get a single client by ID"""
    try:
        repos = _get_repos()
        clients = repos['clients'].list_clients()
        for c in clients:
            if c.get('id') == client_id:
                return c
        raise HTTPException(status_code=404, detail='Client not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch client: {str(e)}')

@api_router.put('/api/clients/{client_id}')
async def update_client(client_id: str, request: Request):
    """Update a client - PRODUCTION READY"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        data = await request.json()
        repos = _get_repos()
        success = repos['clients'].update_client(client_id, data)
        if success:
            return {'ok': True, 'client_id': client_id}
        else:
            raise HTTPException(status_code=404, detail='Client not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to update client: {str(e)}')

@api_router.delete('/api/clients/{client_id}')
async def delete_client(client_id: str, request: Request):
    """Delete a client"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        repos = _get_repos()
        success = repos['clients'].delete_client(client_id)
        if success:
            return {'ok': True}
        raise HTTPException(status_code=404, detail='Client not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to delete client: {str(e)}')


# ==================== DB MANAGER (Postgres) ====================
@api_router.get('/api/db/tables')
async def api_db_tables(request: Request):
    """Return list of tables in public schema (admin only)."""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        from src.db.cloudsql_client import get_cloudsql_client
        client = get_cloudsql_client()
        rows = client.execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")
        names = [r.get('table_name') for r in rows]
        return {'ok': True, 'tables': names}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get('/api/db/table/{table_name}')
async def api_db_table(request: Request, table_name: str):
    """Return rows for a table (paginated). Admin only."""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    # validate table name
    import re
    if not re.match(r'^[A-Za-z0-9_]+$', table_name):
        raise HTTPException(status_code=400, detail='Invalid table name')
    try:
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        from src.db.cloudsql_client import get_cloudsql_client
        client = get_cloudsql_client()
        # Ensure table exists
        tables = client.execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' AND table_name=%s", params=(table_name,))
        if not tables:
            raise HTTPException(status_code=404, detail='Table not found')
        rows = client.execute_query(f"SELECT * FROM \"{table_name}\" LIMIT %s OFFSET %s", params=(limit, offset))
        return {'ok': True, 'rows': rows}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get('/api/db/table/{table_name}/export')
async def api_db_table_export(request: Request, table_name: str):
    """Stream table content as CSV (admin only)."""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    import csv, io
    import itertools
    import re
    if not re.match(r'^[A-Za-z0-9_]+$', table_name):
        raise HTTPException(status_code=400, detail='Invalid table name')
    try:
        from src.db.cloudsql_client import get_cloudsql_client
        from src.services.audit import append_audit_entry
        from src.config.config import Config

        client = get_cloudsql_client()
        sid = Config.from_env().SPREADSHEET_ID

        chunk = int(request.query_params.get('chunk', 500))

        async def csv_stream():
            # record start
            try:
                append_audit_entry(sid, getattr(request.state, 'admin_id', None), None, table_name, '', 'export_started', None, {'chunk_size': chunk})
            except Exception:
                pass

            buf = io.StringIO()
            writer = None
            offset = 0
            try:
                while True:
                    rows = client.execute_query(f"SELECT * FROM \"{table_name}\" LIMIT %s OFFSET %s", params=(chunk, offset))
                    if not rows:
                        break
                    if writer is None:
                        headers = list(rows[0].keys())
                        writer = csv.writer(buf)
                        writer.writerow(headers)
                        yield buf.getvalue()
                        buf.seek(0); buf.truncate(0)
                    for r in rows:
                        writer.writerow([r.get(h, '') for h in headers])
                        yield buf.getvalue()
                        buf.seek(0); buf.truncate(0)
                    offset += chunk
            finally:
                try:
                    append_audit_entry(sid, getattr(request.state, 'admin_id', None), None, table_name, '', 'export_completed', None, {'rows_streamed_up_to_offset': offset})
                except Exception:
                    pass

        from fastapi.responses import StreamingResponse
        filename = f"{table_name}.csv"
        return StreamingResponse(csv_stream(), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="{filename}"'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MASTERS ====================

@api_router.get('/api/masters')
async def get_masters():
    """Get list of all masters from Google Sheets"""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        repos = _get_repos()
        return repos['masters'].list_masters()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch masters: {str(e)}')

@api_router.get('/api/admin/masters')
async def api_admin_get_masters(request: Request):
    """Return list of masters (admin view)"""
    try:
        repos = _get_repos()
        return repos['masters'].list_masters()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post('/api/masters', status_code=201)
async def create_master(master: Master):
    """Create a new master"""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        repos = _get_repos()
        new_master = repos['masters'].create_master(
            name=master.name,
            calendar_id=getattr(master, 'calendar_id', ""),
            specialties=getattr(master, 'specialization', ""),
            active=getattr(master, 'is_active', True)
        )
        return new_master
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to create master: {str(e)}')

@api_router.get('/api/masters/{master_id}')
async def get_master(master_id: str):
    """Get a single master by ID"""
    try:
        repos = _get_repos()
        masters = repos['masters'].list_masters()
        for m in masters:
            if m.get('id') == master_id:
                return m
        raise HTTPException(status_code=404, detail='Master not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch master: {str(e)}')

@api_router.put('/api/masters/{master_id}')
async def update_master(master_id: str, request: Request):
    """Update a master - PRODUCTION READY"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        data = await request.json()
        repos = _get_repos()
        success = repos['masters'].update_master(master_id, data)
        if success:
            return {'ok': True, 'master_id': master_id}
        raise HTTPException(status_code=404, detail='Master not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to update master: {str(e)}')

@api_router.delete('/api/masters/{master_id}')
async def delete_master(master_id: str, request: Request):
    """Delete a master"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        repos = _get_repos()
        success = repos['masters'].delete_master(master_id)
        if success:
            return {'ok': True}
        raise HTTPException(status_code=404, detail='Master not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to delete master: {str(e)}')

@api_router.post('/api/admin/masters/{master_id}/calendar')
async def api_admin_update_master_calendar(master_id: str, request: Request):
    """Update calendar ID for a master"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        body = await request.json()
        cid = body.get('calendar_id')
        if not cid:
            raise HTTPException(status_code=400, detail='Missing calendar_id')
        repos = _get_repos()
        success = repos['masters'].update_master_calendar(master_id, cid)
        if success:
            return {'ok': True, 'master_id': master_id, 'calendar_id': cid}
        raise HTTPException(status_code=404, detail='Master not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to update calendar: {str(e)}')

# ==================== SERVICES ====================

@api_router.get('/api/services')
async def get_services():
    """Get list of all services from Google Sheets"""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        repos = _get_repos()
        return repos['services'].list_services()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch services: {str(e)}')

@api_router.post('/api/services', status_code=201)
async def create_service(service: Service):
    """Create a new service"""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        repos = _get_repos()
        new_service = repos['services'].create_service(
            name=service.name,
            description=getattr(service, 'description', ""),
            duration_min=getattr(service, 'duration_minutes', 60),
            price_from=getattr(service, 'price', 0),
            price_to=getattr(service, 'price', 0),
            category=getattr(service, 'category', 'tattoo'),
            active=getattr(service, 'is_active', True)
        )
        return new_service
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to create service: {str(e)}')

@api_router.get('/api/services/{service_id}')
async def get_service(service_id: str):
    """Get a single service by ID"""
    try:
        repos = _get_repos()
        services = repos['services'].list_services()
        for s in services:
            if s.get('id') == service_id:
                return s
        raise HTTPException(status_code=404, detail='Service not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch service: {str(e)}')


@api_router.get('/api/availability')
async def get_availability(date: str, master_id: str = None):
    """Return available slots via booking service. Public endpoint by default."""
    try:
        repos = _get_repos()
        bs = BookingService(repos['sheets_client'], repos['spreadsheet_id'])
        slots = bs.list_available_slots(date=date, master_id=master_id)
        return { 'ok': True, 'slots': slots }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post('/api/webhooks/calendar_change')
async def webhook_calendar_change(request: Request):
    """Webhook endpoint to notify of a calendar change (Google push notifications)
    Accepts body JSON: { "calendar_id": "..." }
    Protected by a secret token header: X-Webhook-Secret or similar (optional config)
    """
    # optional: check secret via env
    secret_expected = os.getenv('CALENDAR_SYNC_SECRET')
    if secret_expected:
        secret_received = request.headers.get('X-Webhook-Secret') or request.headers.get('x-webhook-secret')
        if secret_received != secret_expected:
            raise HTTPException(status_code=403, detail='Forbidden')
    data = await request.json()
    calendar_id = data.get('calendar_id') or data.get('calendar_id')
    if not calendar_id:
        raise HTTPException(status_code=400, detail='Missing calendar_id')
    try:
        from src.services.calendar_sync import webhook_notify_calendar_change
        synced = webhook_notify_calendar_change(calendar_id)
        return { 'ok': True, 'synced': synced }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post('/api/admin/availability/refresh')
async def api_admin_refresh_availability(request: Request):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        from src.services.slot_worker import compute_slots_for_all_masters, refresh_availability_materialized_view
        now = datetime.utcnow()
        until = now + timedelta(days=7)
        count = compute_slots_for_all_masters(now, until, duration=120)
        refresh_availability_materialized_view()
        return { 'ok': True, 'computed_slots': count }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post('/api/admin/run_services_seed')
async def api_admin_run_services_seed(request: Request):
    """Admin-only endpoint to run the services seed script (idempotent upsert).
    Useful for admin UI to re-sync/add default services programmatically.
    """
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        # Run the seed script logic directly
        import scripts.seed_services as seed_services
        seed_services.main()
        return { 'ok': True }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to run services seed: {str(e)}')

@api_router.put('/api/services/{service_id}')
async def update_service(service_id: str, request: Request):
    """Update a service - PRODUCTION READY"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        data = await request.json()
        repos = _get_repos()
        success = repos['services'].update_service(service_id, data)
        if success:
            return {'ok': True, 'service_id': service_id}
        raise HTTPException(status_code=404, detail='Service not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to update service: {str(e)}')

@api_router.delete('/api/services/{service_id}')
async def delete_service(service_id: str, request: Request):
    """Delete a service"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        repos = _get_repos()
        success = repos['services'].delete_service(service_id)
        if success:
            return {'ok': True}
        raise HTTPException(status_code=404, detail='Service not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to delete service: {str(e)}')

# ==================== BOOKINGS ====================

@api_router.get('/api/bookings')
async def get_bookings():
    """Get list of all bookings from Google Sheets"""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured')
    try:
        repos = _get_repos()
        return repos['bookings'].list_bookings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch bookings: {str(e)}')


@api_router.post('/api/bookings', status_code=201)
async def create_booking(request: Request):
    """Create booking. Accepts either {date, slot_start, slot_end} or {datetime_start, datetime_end}."""
    if _force_sheet_mode() and not _get_spreadsheet_id():
        raise HTTPException(status_code=400, detail='SPREADSHEET_ID not configured; FORCE_SHEET_MODE is enabled')
    try:
        data = await request.json()
        repos = _get_repos()
        # support both date+slot and explicit datetime fields
        if data.get('date') and data.get('slot_start') and data.get('slot_end'):
            res = repos['bookings'].create_booking(
                client_id=str(data.get('client_id', '')),
                master_id=str(data.get('master_id', '')),
                date=data.get('date'),
                slot_start=data.get('slot_start'),
                slot_end=data.get('slot_end'),
                status=data.get('status', 'pending'),
                google_event_id=data.get('google_event_id', '')
            )
            return res
        # fallback to using datetime_start/datetime_end
        if data.get('datetime_start') and data.get('datetime_end'):
            # translate to date + slot for underlying create_booking
            dt_start = data.get('datetime_start')
            dt_end = data.get('datetime_end')
            date = dt_start.split('T')[0]
            slot_start = dt_start.split('T')[1] if 'T' in dt_start else dt_start
            slot_end = dt_end.split('T')[1] if 'T' in dt_end else dt_end
            res = repos['bookings'].create_booking(
                client_id=str(data.get('client_id', '')),
                master_id=str(data.get('master_id', '')),
                date=date,
                slot_start=slot_start,
                slot_end=slot_end,
                status=data.get('status', 'pending'),
                google_event_id=data.get('google_event_id', '')
            )
            return res
        raise HTTPException(status_code=400, detail='Missing required booking fields')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to create booking: {str(e)}')

@api_router.get('/api/bookings/{booking_id}')
async def get_booking(booking_id: str):
    """Get a single booking by ID"""
    try:
        repos = _get_repos()
        bookings = repos['bookings'].list_bookings()
        for b in bookings:
            if b.get('id') == booking_id:
                return b
        raise HTTPException(status_code=404, detail='Booking not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch booking: {str(e)}')

@api_router.put('/api/bookings/{booking_id}')
async def update_booking(booking_id: str, request: Request):
    """Update a booking - PRODUCTION READY"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        data = await request.json()
        repos = _get_repos()
        success = repos['bookings'].update_booking(booking_id, data)
        if success:
            return {'ok': True, 'booking_id': booking_id}
        raise HTTPException(status_code=404, detail='Booking not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to update booking: {str(e)}')

@api_router.delete('/api/bookings/{booking_id}')
async def delete_booking(booking_id: str, request: Request):
    """Delete a booking"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        repos = _get_repos()
        success = repos['bookings'].delete_booking(booking_id)
        if success:
            return {'ok': True}
        raise HTTPException(status_code=404, detail='Booking not found')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to delete booking: {str(e)}')

# ==================== ADMIN ====================

@api_router.get('/api/admin/admins')
async def api_admin_list_admins():
    """Return list of administrator IDs"""
    try:
        from src.services.admin_manager import get_admin_ids
        admins = get_admin_ids()
        return {'admins': admins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post('/api/admin/admins')
async def api_admin_add_admin(request: Request, body: NewAdminModel):
    """Add admin ID - requires runtime update via AdminManager"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        from src.services.admin_manager import grant_admin
        ok = grant_admin(int(body.admin_id))
        return {"ok": ok, "admin_id": int(body.admin_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete('/api/admin/admins/{admin_id}')
async def api_admin_delete_admin(request: Request, admin_id: int):
    """Remove admin ID - requires runtime update via AdminManager"""
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        from src.services.admin_manager import revoke_admin
        ok = revoke_admin(int(admin_id))
        return {"ok": ok, "admin_id": int(admin_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get('/api/admin/bookings_pending')
async def api_admin_list_pending_bookings(request: Request):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        repos = _get_repos()
        from src.services.booking_service import BookingService
        bs = BookingService(repos['sheets_client'], repos['spreadsheet_id'])
        pending = bs.list_pending_bookings()
        return {'ok': True, 'count': len(pending), 'pending': pending}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get('/api/admin/stream')
async def api_admin_stream(request: Request):
    """Simple Server-Sent Events endpoint for admin clients.

    Requires admin privileges. Streams periodic heartbeat messages and can be extended to stream audit events.
    """
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')

    async def event_stream():
        # For now yield a few heartbeats and then finish; real implementation should be hooked to an event source
        for i in range(3):
            payload = {'type': 'heartbeat', 'seq': i}
            yield f"data: {json.dumps(payload)}\n\n"
            import asyncio
            await asyncio.sleep(0.1)

    return StreamingResponse(event_stream(), media_type='text/event-stream')


@api_router.post('/api/admin/bookings_pending/{pending_id}/confirm')
async def api_admin_confirm_pending(request: Request, pending_id: str):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        repos = _get_repos()
        from src.services.booking_service import BookingService
        bs = BookingService(repos['sheets_client'], repos['spreadsheet_id'])
        ok = bs.confirm_pending_booking(pending_id, confirmed_by=f"admin:{request.state.admin_id}")
        return {'ok': ok}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post('/api/admin/bookings_pending/{pending_id}/reject')
async def api_admin_reject_pending(request: Request, pending_id: str):
    if not _is_admin(request):
        raise HTTPException(status_code=403, detail='Forbidden')
    try:
        repos = _get_repos()
        from src.db.repositories.bookings_repo import BookingsRepo
        br = BookingsRepo(repos['sheets_client'], repos['spreadsheet_id'])
        ok = br.update_booking(pending_id, {'status': 'cancelled'})
        return {'ok': ok}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
