"""
Service factories - создают экземпляры сервисов с подключением к БД
"""

import logging
from typing import Optional

from src.db.sheets_client import SheetsClient
from src.services.booking_service import BookingService
from src.services.calendar_service import CalendarService
from src.services.client_service import ClientService
from src.services.admin_service import AdminService
from src.services.master_service import MasterService
from src.config.config import Config
from src.config.env_loader import load_env

logger = logging.getLogger(__name__)

# Глобальные экземпляры
_sheets_client: Optional[SheetsClient] = None
_booking_service: Optional[BookingService] = None
_calendar_service: Optional[CalendarService] = None
_client_service: Optional[ClientService] = None
_admin_service: Optional[AdminService] = None
_master_service: Optional[MasterService] = None


def get_sheets_client() -> SheetsClient:
    """Получить или создать sheets client"""
    global _sheets_client
    if _sheets_client is None:
        try:
            load_env()
            cfg = Config.from_env()
            _sheets_client = SheetsClient(
                creds_path=cfg.GOOGLE_CREDENTIALS_PATH,
                token_path=cfg.GOOGLE_TOKEN_PATH
            )
            logger.info("✅ Sheets client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize sheets client: {e}")
            raise
    return _sheets_client


def get_booking_service() -> BookingService:
    """Получить или создать booking service"""
    global _booking_service
    if _booking_service is None:
        sheets_client = get_sheets_client()
        cfg = Config.from_env()
        _booking_service = BookingService(
            sheets_client=sheets_client,
            spreadsheet_id=cfg.SPREADSHEET_ID
        )
        logger.info("✅ Booking service initialized")
    return _booking_service


def get_calendar_service() -> CalendarService:
    """Получить или создать calendar service"""
    global _calendar_service
    if _calendar_service is None:
        sheets_client = get_sheets_client()
        _calendar_service = CalendarService(sheets_client=sheets_client)
        logger.info("✅ Calendar service initialized")
    return _calendar_service


def get_client_service() -> ClientService:
    """Получить или создать client service"""
    global _client_service
    if _client_service is None:
        sheets_client = get_sheets_client()
        cfg = Config.from_env()
        _client_service = ClientService(
            sheets_client=sheets_client,
            spreadsheet_id=cfg.SPREADSHEET_ID
        )
        logger.info("✅ Client service initialized")
    return _client_service


def get_admin_service() -> AdminService:
    """Получить или создать admin service"""
    global _admin_service
    if _admin_service is None:
        sheets_client = get_sheets_client()
        cfg = Config.from_env()
        _admin_service = AdminService(
            sheets_client=sheets_client,
            spreadsheet_id=cfg.SPREADSHEET_ID
        )
        logger.info("✅ Admin service initialized")
    return _admin_service


def get_master_service() -> MasterService:
    """Получить или создать master service"""
    global _master_service
    if _master_service is None:
        sheets_client = get_sheets_client()
        cfg = Config.from_env()
        _master_service = MasterService(
            sheets_client=sheets_client,
            spreadsheet_id=cfg.SPREADSHEET_ID
        )
        logger.info("✅ Master service initialized")
    return _master_service


# Export
__all__ = [
    "get_sheets_client",
    "get_booking_service",
    "get_calendar_service",
    "get_client_service",
    "get_admin_service",
    "get_master_service"
]
