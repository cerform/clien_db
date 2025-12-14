from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from src.services.db_admin import list_rows, get_row, update_row, append_row, delete_row
from src.services.audit import append_audit_entry, list_audit_for_row, get_latest_audit_for_row
from src.services.admin_manager import is_admin as is_admin_service

router = APIRouter()


@router.get('/admin/db', response_class=HTMLResponse)
async def admin_db_page(request: Request):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        return HTMLResponse('Forbidden', status_code=403)
    return request.app.templates.TemplateResponse('admin_db.html', {'request': request})


@router.get('/api/admin/db/{sheet_name}')
async def api_list_rows(request: Request, sheet_name: str):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    try:
        rows = list_rows(sheet_name)
        return {'ok': True, 'rows': rows}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.get('/api/admin/db/{sheet_name}/{row_id}')
async def api_get_row(request: Request, sheet_name: str, row_id: str):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    try:
        r = get_row(sheet_name, row_id)
        return {'ok': True, 'row': r}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.put('/api/admin/db/{sheet_name}/{row_id}')
async def api_update_row(request: Request, sheet_name: str, row_id: str):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    body = await request.json()
    try:
        # capture before
        from src.config.config import Config
        sid = Config.from_env().SPREADSHEET_ID
        before = get_row(sheet_name, row_id)
        ok = update_row(sheet_name, row_id, body)
        # audit
        append_audit_entry(sid, getattr(request.state, 'admin_id', None), None, sheet_name, row_id, 'update', before, body)
        return {'ok': ok}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.post('/api/admin/db/{sheet_name}')
async def api_append_row(request: Request, sheet_name: str):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    body = await request.json()
    try:
        row = append_row(sheet_name, body)
        from src.config.config import Config
        sid = Config.from_env().SPREADSHEET_ID
        append_audit_entry(sid, getattr(request.state, 'admin_id', None), None, sheet_name, body.get('id', ''), 'create', None, body)
        return {'ok': True, 'row': row}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.delete('/api/admin/db/{sheet_name}/{row_id}')
async def api_delete_row(request: Request, sheet_name: str, row_id: str):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    try:
        from src.config.config import Config
        sid = Config.from_env().SPREADSHEET_ID
        before = get_row(sheet_name, row_id)
        ok = delete_row(sheet_name, row_id)
        append_audit_entry(sid, getattr(request.state, 'admin_id', None), None, sheet_name, row_id, 'delete', before, None)
        return {'ok': ok}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.get('/api/admin/db/{sheet_name}/{row_id}/audit')
async def api_list_audit(request: Request, sheet_name: str, row_id: str):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    from src.config.config import Config
    sid = Config.from_env().SPREADSHEET_ID
    # Pagination params
    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 25))
        if page < 1:
            page = 1
        offset = (page - 1) * page_size
    except Exception:
        offset = 0
        page_size = 25

    fmt = request.query_params.get('format', 'json')
    try:
        paged = list_audit_for_row(sid, sheet_name, row_id, offset=offset, limit=page_size)
        if fmt == 'csv':
            # return CSV text
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf)
            # header
            writer.writerow(['timestamp','user_id','user_name','sheet','row_id','action','before','after'])
            for it in paged['items']:
                writer.writerow([it.get('timestamp'), it.get('user_id'), it.get('user_name'), it.get('sheet'), it.get('row_id'), it.get('action'), it.get('before'), it.get('after')])
            return HTMLResponse(content=buf.getvalue(), media_type='text/csv')
        return {'ok': True, 'total': paged['total'], 'items': paged['items'], 'page': page, 'page_size': page_size}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.post('/api/admin/db/rollback')
async def api_rollback(request: Request):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    body = await request.json()
    sheet_name = body.get('sheet')
    row_id = body.get('row_id')
    ts = body.get('timestamp')
    from src.config.config import Config
    sid = Config.from_env().SPREADSHEET_ID
    try:
        # Find audit entries and pick matching timestamp or latest
        paged = list_audit_for_row(sid, sheet_name, row_id, offset=0, limit=1000)
        audit_rows = paged.get('items', [])
        target = None
        if ts:
            for a in audit_rows:
                if a.get('timestamp') == ts:
                    target = a
                    break
        if not target and audit_rows:
            target = audit_rows[-1]
        if not target:
            return {'ok': False, 'error': 'No audit entry found'}
        before_json = target.get('before') or '{}'
        import json
        before = json.loads(before_json)
        if not before:
            return {'ok': False, 'error': 'No before state to rollback to'}
        ok = update_row(sheet_name, row_id, before)
        append_audit_entry(sid, getattr(request.state, 'admin_id', None), None, sheet_name, row_id, 'rollback', get_row(sheet_name, row_id), before)
        return {'ok': ok}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@router.post('/api/admin/sync-admins')
async def api_sync_admins(request: Request):
    if not is_admin_service(getattr(request.state, 'admin_id', None)):
        raise JSONResponse({'detail': 'Forbidden'}, status_code=403)
    try:
        from src.services.admin_sync import sync_admins_to_sheet
        from src.core.config_manager import get_config
        cfg = get_config()
        sid = cfg.get('spreadsheet_id')
        res = sync_admins_to_sheet(sid)
        return res
    except Exception as e:
        return {'ok': False, 'error': str(e)}
