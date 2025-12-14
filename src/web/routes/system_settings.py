from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from src.core.config_manager import get_config, save_config, save_config_to_sheet, load_config_from_sheet, set_secret, get_secret
from src.db.sheets_client import SheetsClient
from src.services.google_sheets_initializer import ensure_sheets_structure
from src.services.sheets_migrator import migrate_spreadsheet
from src.core.llm_client import LLMClient
from aiogram import Bot
from src.config.config import Config
from src.services.admin_manager import is_admin as is_admin_service

router = APIRouter(prefix="/admin", tags=["admin_settings"])  # mounted at /admin


@router.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    cfg = get_config()
    # Compose a status summary
    status = {
        "sheets_ok": False,
        "telegram_ok": False,
        "llm_ok": False,
    }
    spreadsheet_id = cfg.get("spreadsheet_id") or request.app.state.config.SPREADSHEET_ID
    # check sheets
    try:
        sc = SheetsClient()
        sc.read_sheet(spreadsheet_id, "clients")
        status["sheets_ok"] = True
    except Exception:
        status["sheets_ok"] = False
    # check telegram
    try:
        token = get_secret("TELEGRAM_BOT_TOKEN") or cfg.get("telegram_token") or request.app.state.config.BOT_TOKEN
        b = Bot(token=token) if token else None
        if b:
            try:
                await b.get_me()
                status["telegram_ok"] = True
            except Exception:
                status["telegram_ok"] = False
    except Exception:
        status["telegram_ok"] = False
    # check llm
    try:
        provider = cfg.get("llm_provider") or "openai"
        api_key = get_secret("LLM_API_KEY") or cfg.get("llm_api_key") or request.app.state.config.OPENAI_API_KEY
        llm = LLMClient(provider=provider, api_key=api_key)
        llm_ok = True if llm.generate_admin_reply("ping", "ping") else True
        status["llm_ok"] = bool(llm_ok)
    except Exception:
        status["llm_ok"] = False

    # Provide current config values for rendering
    current_config = get_config()
    # Merge env config
    envcfg = Config.from_env()
    current_config.update({
        "spreadsheet_id": current_config.get("spreadsheet_id") or envcfg.SPREADSHEET_ID,
        "calendar_id": current_config.get("calendar_id") or envcfg.MASTER_CALENDAR_ID,
    })
    return request.app.templates.TemplateResponse(request, "settings.html", {"request": request, "config": current_config, "status": status})


@router.post("/settings/save")
async def settings_save(request: Request):
    # Save only non-secret fields
    form = await request.form()
    salon_name = form.get('salon_name')
    timezone = form.get('timezone')
    spreadsheet_id = form.get('spreadsheet_id')
    calendar_id = form.get('calendar_id')
    admin_ids = form.get('admin_ids')

    cfg = get_config()
    if salon_name:
        cfg["salon_name"] = salon_name
    if timezone:
        cfg["timezone"] = timezone
    if spreadsheet_id:
        cfg["spreadsheet_id"] = spreadsheet_id
    if calendar_id:
        cfg["calendar_id"] = calendar_id
    if admin_ids:
        cfg["admin_ids"] = [int(i.strip()) for i in admin_ids.split(",") if i.strip()]
    save_config(cfg)
    # store into sheet too
    try:
        sc = SheetsClient()
        save_config_to_sheet(sc, cfg.get("spreadsheet_id"), {k: v for k, v in cfg.items() if k not in ("llm_api_key", "telegram_token")})
    except Exception:
        pass
    # Try to auto-configure webhook if bot token is present
    try:
        token = get_secret("TELEGRAM_BOT_TOKEN") or cfg.get("telegram_token") or request.app.state.config.BOT_TOKEN
        if token:
            # Import setup_webhook lazily to avoid circular imports
            try:
                from run_production import setup_webhook
                await setup_webhook()
            except Exception:
                # If direct import/call fails, attempt to call local endpoint as fallback
                try:
                    import httpx
                    # Use relative URL on same host
                    base = str(request.base_url).rstrip("/")
                    await httpx.AsyncClient().post(f"{base}/api/setup-webhook", timeout=10)
                except Exception:
                    # best-effort only
                    pass

    except Exception:
        # non-fatal
        pass

    # If minimal configuration is present, redirect to homepage; otherwise show settings page
    if cfg.get("spreadsheet_id") and (get_secret("TELEGRAM_BOT_TOKEN") or cfg.get("telegram_token") or request.app.state.config.BOT_TOKEN):
        return RedirectResponse(url="/", status_code=302)
    return RedirectResponse(url="/admin/settings", status_code=302)


@router.post("/settings/migrate")
async def settings_migrate(request: Request):
    # Simple admin check: require admin_id to be in configured ADMIN_USER_IDS in env
    cfg = get_config()
    envcfg = Config.from_env()
    try:
        sc = SheetsClient()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot initialize Sheets client: {e}")

    spreadsheet_id = cfg.get("spreadsheet_id") or envcfg.SPREADSHEET_ID
    if not spreadsheet_id:
        raise HTTPException(status_code=400, detail="spreadsheet_id not configured")

    # check admin ID either from Authorization token or form
    claimed_admin_id = None
    if hasattr(request, 'state') and getattr(request.state, 'admin_id', None):
        claimed_admin_id = request.state.admin_id
    else:
        form = await request.form()
        admin_id = form.get('admin_id')
        if admin_id:
            claimed_admin_id = int(admin_id)
    if claimed_admin_id and is_admin_service(claimed_admin_id):
        result = migrate_spreadsheet(sc, spreadsheet_id)
        return JSONResponse(content={"ok": True, "result": result})
    raise HTTPException(status_code=403, detail="Forbidden: admin_id not recognized")


@router.post('/settings/test')
async def settings_test(request: Request):
    """Send a test Telegram message to a chat id. Requires admin privileges (admin_id param or Authorization header).

    This endpoint is intended for quick verification that webhook / bot connectivity works and that the bot can send messages.
    """
    # Determine claimed admin id
    form = await request.form()
    chat_id = form.get('chat_id')
    text = form.get('text') or 'Test message from INKA'
    admin_id = form.get('admin_id')
    claimed_admin_id = getattr(request.state, 'admin_id', None)
    if not claimed_admin_id and admin_id:
        claimed_admin_id = int(admin_id)

    if not claimed_admin_id or not is_admin_service(claimed_admin_id):
        raise HTTPException(status_code=403, detail='Forbidden: admin_id not recognized')

    # Get bot token
    cfg = get_config()
    token = get_secret('TELEGRAM_BOT_TOKEN') or cfg.get('telegram_token') or request.app.state.config.BOT_TOKEN
    if not token:
        raise HTTPException(status_code=400, detail='Bot token not configured')

    # Send a message using aiogram Bot (async)
    try:
        bot = Bot(token=token)
        res = await bot.send_message(chat_id=chat_id, text=text)
        return JSONResponse({'ok': True, 'result': {'chat_id': res.chat.id, 'message_id': res.message_id}})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@router.get('/bookings/pending', response_class=HTMLResponse)
async def admin_pending_bookings(request: Request):
    # Require admin
    if not getattr(request.state, 'admin_id', None):
        return RedirectResponse('/login')
    # Fetch pending bookings (via service)
    from src.core.config_manager import get_config
    try:
        from src.services.booking_service import BookingService
        sc = SheetsClient()
        cfg = get_config()
        bs = BookingService(sc, cfg.get('spreadsheet_id'))
        pending = bs.list_pending_bookings()
    except Exception:
        pending = []
    return request.app.templates.TemplateResponse(request, 'pending_bookings.html', {'request': request, 'pending': pending})


@router.post('/bookings/pending/{pending_id}/confirm')
async def admin_confirm_pending(request: Request, pending_id: str):
    if not getattr(request.state, 'admin_id', None):
        return RedirectResponse('/login')
    from src.core.config_manager import get_config
    sc = SheetsClient()
    cfg = get_config()
    bs = BookingService(sc, cfg.get('spreadsheet_id'))
    ok = bs.confirm_pending_booking(pending_id, confirmed_by=f"admin:{request.state.admin_id}")
    return RedirectResponse('/admin/bookings/pending')


@router.post('/bookings/pending/{pending_id}/reject')
async def admin_reject_pending(request: Request, pending_id: str):
    if not getattr(request.state, 'admin_id', None):
        return RedirectResponse('/login')
    from src.core.config_manager import get_config
    sc = SheetsClient()
    cfg = get_config()
    from src.db.repositories.bookings_repo import BookingsRepo
    br = BookingsRepo(sc, cfg.get('spreadsheet_id'))
    br.update_booking(pending_id, {'status': 'cancelled'})
    return RedirectResponse('/admin/bookings/pending')


@router.post("/masters/update_calendar")
async def update_master_calendar(request: Request):
    """Admin endpoint to update a master's calendar ID in Google Sheets.

    Requires admin token via Authorization: Bearer <token> or admin_id form field.
    """
    envcfg = Config.from_env()
    # verify admin id either via token or param
    body = await request.form()
    master_id = body.get('master_id')
    calendar_id = body.get('calendar_id')
    claimed_admin_id = getattr(request.state, 'admin_id', None)
    if not claimed_admin_id:
        # fallback to admin_id in form if provided
        claimed_admin_id = int(body.get('admin_id')) if body.get('admin_id') else None
    if not claimed_admin_id or not is_admin_service(claimed_admin_id):
        raise HTTPException(status_code=403, detail="Forbidden: admin_id not recognized")
    try:
        sc = SheetsClient()
        from src.db.repositories.masters_repo import MastersRepo
        repo = MastersRepo(sc, os.getenv('SPREADSHEET_ID') or "")
        if not repo.spreadsheet_id:
            raise HTTPException(status_code=400, detail='Spreadsheet not configured')
        ok = repo.update_master_calendar(master_id, calendar_id)
        if not ok:
            raise HTTPException(status_code=404, detail='Master not found')
        return JSONResponse({'ok': True, 'master_id': master_id, 'calendar_id': calendar_id})
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)
