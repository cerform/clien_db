from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from src.core.config_manager import get_config, save_config, is_configured, set_secret, get_secret
from src.db.sheets_client import SheetsClient
from src.core.llm_client import LLMClient
from aiogram import Bot
from src.services.google_sheets_initializer import ensure_sheets_structure

router = APIRouter()

@router.get("/setup", response_class=HTMLResponse)
async def setup_get(request: Request):
    if is_configured():
        return RedirectResponse("/admin")
    return request.app.templates.TemplateResponse("setup.html", {"request": request, "step": 1})

@router.post("/setup", response_class=HTMLResponse)
async def setup_post(
    request: Request,
    salon_name: str = Form(...),
    timezone: str = Form(...),
    spreadsheet_id: str = Form(...),
    calendar_id: str = Form(...),
    telegram_token: str = Form(...),
    admin_ids: str = Form(...),
    llm_provider: str = Form(...),
    llm_api_key: str = Form(...),
    create_spreadsheet: str = Form(None),
):
    config = {
        "salon_name": salon_name,
        "timezone": timezone,
        "spreadsheet_id": spreadsheet_id,
        "calendar_id": calendar_id,
        "telegram_token": telegram_token,
        "admin_ids": [i.strip() for i in admin_ids.split(",")],
        "llm_provider": llm_provider,
        "setup_complete": True
    }
    # Optionally create a new spreadsheet if requested
    if create_spreadsheet and create_spreadsheet.lower() in ("1", "true", "yes"):
        try:
            sc = SheetsClient()
            new_id = sc.create_spreadsheet_template(title=f"{salon_name}_db")
            spreadsheet_id = new_id
        except Exception:
            pass

    # Validate Google Sheets access
    sheets_ok = True
    try:
        sc = SheetsClient()
        # quick check: read the sheet head
        sc.read_sheet(spreadsheet_id, "clients")
    except Exception:
        sheets_ok = False

    # Validate Telegram bot token
    try:
        b = Bot(token=telegram_token)
        me = b.get_me()
        telegram_ok = True
    except Exception:
        telegram_ok = False

    # Validate LLM (if provided)
    try:
        llm_client = LLMClient(provider=llm_provider, api_key=llm_api_key)
        llm_ok = True if llm_client.generate_admin_reply("ping", "ping") else True
    except Exception:
        llm_ok = False

    if not (sheets_ok and telegram_ok and llm_ok):
        return request.app.templates.TemplateResponse("setup.html", {"request": request, "error": "Validation failed. Check your keys and access permissions."})

    # Save config and secrets
    save_config(config)
    set_secret("TELEGRAM_BOT_TOKEN", telegram_token)
    set_secret("LLM_API_KEY", llm_api_key)
    # Initialize spreadsheet structure (create sheets and headers if needed)
    try:
        sc = SheetsClient()
        ensure_sheets_structure(sc, spreadsheet_id)
        # Save non-secret config values to sheet
        try:
            from src.core.config_manager import save_config_to_sheet
            save_config_to_sheet(sc, spreadsheet_id, {k: v for k, v in config.items() if k not in ("telegram_token", "llm_api_key")})
        except Exception:
            pass
    except Exception as e:
        # If the initialization fails, log and continue; user can run migration later
        try:
            import logging
            logging.getLogger(__name__).warning(f"Spreadsheet structure initialization failed: {e}")
        except Exception:
            pass
    # Set Telegram webhook to current service base URL
    try:
        base = str(request.base_url).rstrip("/")
        webhook_url = f"{base}/telegram/webhook"
        # aiogram Bot.set_webhook is async — await it
        await b.set_webhook(webhook_url)
    except Exception:
        # ignore: some environments may not be able to contact external Telegram API
        pass

    return RedirectResponse("/admin", status_code=302)
