"""Admin pages router (minimal version) for INKA

This module provides the minimal admin routes used in tests and for the basic setup UI.
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

templates = Jinja2Templates(directory=str((Path(__file__).parent / "templates")))
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.get("", response_class=HTMLResponse)
async def admin_root(request: Request):
    return RedirectResponse(url="/setup", status_code=302)


@admin_router.get("/", response_class=HTMLResponse)
async def admin_slash(request: Request):
    return RedirectResponse(url="/setup", status_code=302)


@admin_router.get("/setup", response_class=HTMLResponse)
async def admin_setup(request: Request):
    return templates.TemplateResponse(request, "setup.html", {"request": request})


@admin_router.get("/style-demo", response_class=HTMLResponse)
async def admin_style_demo(request: Request):
    return templates.TemplateResponse(request, "style_demo.html", {"request": request})


@admin_router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """Calendar integration page"""
    from src.config.config import Config
    config = Config.from_env()
    calendar_id = config.MASTER_CALENDAR_ID if hasattr(config, 'MASTER_CALENDAR_ID') else None
    return templates.TemplateResponse(request, "calendar.html", {
        "request": request,
        "calendar_id": calendar_id
    })


@admin_router.get("/endpoints", response_class=HTMLResponse)
async def endpoints_page(request: Request):
    """Render the API endpoints explorer + status UI"""
    return templates.TemplateResponse(request, "endpoints.html", {"request": request})


@admin_router.get("/calendar-settings", response_class=HTMLResponse)
async def calendar_settings_page(request: Request):
    # Provide service account email to the template so masters can add it to their calendars
    import os
    service_account = os.getenv('GOOGLE_SERVICE_ACCOUNT') or os.getenv('SERVICE_ACCOUNT_EMAIL') or ''
    return templates.TemplateResponse(request, "calendar_settings.html", {"request": request, "service_account": service_account})
