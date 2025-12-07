"""
🔍 Debug Handler - Administrative diagnostic commands
Provides real-time configuration and access diagnostics to admins
"""

from aiogram import Router, F
from aiogram.types import Message
from pathlib import Path
from datetime import datetime
import logging

from src.config import get_config
from src.db.sheets_client import GoogleSheetsClient
from src.calendars.google_calendar_sync import GoogleCalendarSync

logger = logging.getLogger(__name__)

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    try:
        config = get_config()
        return user_id in config.admin_ids
    except:
        return False


@router.message(F.text == "/debug_config")
async def debug_config_handler(message: Message):
    """
    /debug_config - Show full configuration diagnostics
    Admin only command
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return
    
    try:
        config = get_config()
        
        # Build configuration report
        report = "🔍 <b>КОНФИГУРАЦИЯ БОТА</b>\n\n"
        
        # Environment
        report += "<b>📋 Переменные окружения:</b>\n"
        report += f"• Telegram токен: {'✅' if config.telegram_bot_token else '❌'}\n"
        report += f"• Google Spreadsheet ID: ✅\n"
        report += f"• Google Calendar ID: {'✅' if config.google_calendar_id else '❌'}\n"
        report += f"• OpenAI API: {'✅' if config.openai_api_key else '❌'}\n"
        report += f"• Timezone: {config.timezone}\n"
        report += f"• Admin IDs: {len(config.admin_ids)} шт.\n\n"
        
        # Credentials
        report += "<b>🔐 Учетные данные:</b>\n"
        if Path("credentials.json").exists():
            report += "• Local credentials.json: ✅\n"
        else:
            report += "• Local credentials.json: ❌ (using Cloud Run Service Account)\n"
        report += "\n"
        
        # Google Sheets
        report += "<b>📊 Google Sheets:</b>\n"
        try:
            sheets_client = GoogleSheetsClient(
                credentials_file="credentials.json" if Path("credentials.json").exists() else None,
                spreadsheet_id=config.google_spreadsheet_id
            )
            sheets = sheets_client.service.spreadsheets().get(
                spreadsheetId=config.google_spreadsheet_id
            ).execute()
            sheet_names = [s['properties']['title'] for s in sheets.get('sheets', [])]
            
            report += f"• Spreadsheet: ✅ ({sheets['properties']['title']})\n"
            report += f"• Sheets: {len(sheet_names)}\n"
            
            # Check for required sheets
            required = {'clients', 'masters', 'services', 'bookings'}
            found = set(sheet_names)
            if required.issubset(found):
                report += "• All required sheets: ✅\n"
            else:
                missing = required - found
                report += f"• Missing sheets: ❌ ({', '.join(missing)})\n"
        except Exception as e:
            report += f"• Spreadsheet: ❌ ({str(e)[:50]})\n"
        
        report += "\n"
        
        # Google Calendar
        report += "<b>📅 Google Calendar:</b>\n"
        try:
            calendar_client = GoogleCalendarSync(
                credentials_file="credentials.json" if Path("credentials.json").exists() else None,
                calendar_id=config.google_calendar_id
            )
            calendar_client.service.events().list(
                calendarId=config.google_calendar_id,
                maxResults=1
            ).execute()
            report += f"• Calendar: ✅\n"
        except Exception as e:
            report += f"• Calendar: ❌ ({str(e)[:50]})\n"
        
        report += "\n"
        
        # Admin IDs
        report += "<b>👤 Администраторы:</b>\n"
        for admin_id in config.admin_ids:
            report += f"• {admin_id}\n"
        
        report += f"\n<b>⏰ Время проверки:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await message.answer(report, parse_mode="HTML")
        logger.info(f"Admin {message.from_user.id} requested debug config")
    
    except Exception as e:
        logger.error(f"Error in debug_config: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)[:200]}")


@router.message(F.text == "/debug_sheets")
async def debug_sheets_handler(message: Message):
    """
    /debug_sheets - Show Google Sheets diagnostics
    Admin only command
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return
    
    try:
        config = get_config()
        sheets_client = GoogleSheetsClient(
            credentials_file="credentials.json" if Path("credentials.json").exists() else None,
            spreadsheet_id=config.google_spreadsheet_id
        )
        
        sheets = sheets_client.service.spreadsheets().get(
            spreadsheetId=config.google_spreadsheet_id
        ).execute()
        
        report = "📊 <b>GOOGLE SHEETS ДИАГНОСТИКА</b>\n\n"
        
        # Spreadsheet info
        props = sheets['properties']
        report += f"<b>Spreadsheet:</b> {props['title']}\n"
        report += f"<b>ID:</b> <code>{config.google_spreadsheet_id}</code>\n\n"
        
        # Sheets list with row counts
        report += "<b>📑 Листы в документе:</b>\n"
        for i, sheet in enumerate(sheets.get('sheets', [])):
            title = sheet['properties']['title']
            grid_props = sheet['properties'].get('gridProperties', {})
            rows = grid_props.get('rowCount', '?')
            cols = grid_props.get('columnCount', '?')
            report += f"{i+1}. <b>{title}</b> ({rows}×{cols})\n"
        
        await message.answer(report, parse_mode="HTML")
        logger.info(f"Admin {message.from_user.id} requested sheets debug")
    
    except Exception as e:
        logger.error(f"Error in debug_sheets: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)[:200]}")


@router.message(F.text == "/debug_calendar")
async def debug_calendar_handler(message: Message):
    """
    /debug_calendar - Show Google Calendar diagnostics
    Admin only command
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return
    
    try:
        config = get_config()
        if not config.google_calendar_id:
            await message.answer("❌ Google Calendar не настроен в конфигурации")
            return
        
        calendar_client = GoogleCalendarSync(
            credentials_file="credentials.json" if Path("credentials.json").exists() else None,
            calendar_id=config.google_calendar_id
        )
        
        report = "📅 <b>GOOGLE CALENDAR ДИАГНОСТИКА</b>\n\n"
        
        # Calendar info
        calendar = calendar_client.service.calendarList().get(
            calendarId=config.google_calendar_id
        ).execute()
        
        report += f"<b>Calendar:</b> {calendar.get('summary', 'Unknown')}\n"
        report += f"<b>ID:</b> <code>{config.google_calendar_id}</code>\n"
        report += f"<b>Timezone:</b> {calendar.get('timeZone', 'Unknown')}\n"
        report += f"<b>Access Role:</b> {calendar.get('accessRole', 'Unknown')}\n\n"
        
        # Recent events
        events = calendar_client.service.events().list(
            calendarId=config.google_calendar_id,
            maxResults=5,
            orderBy='startTime',
            singleEvents=True
        ).execute()
        
        report += f"<b>📋 Ближайшие события:</b> {len(events.get('items', []))}\n"
        for event in events.get('items', [])[:3]:
            start = event['start'].get('dateTime', event['start'].get('date', 'Unknown'))
            title = event.get('summary', 'No title')
            report += f"• {start}: {title}\n"
        
        await message.answer(report, parse_mode="HTML")
        logger.info(f"Admin {message.from_user.id} requested calendar debug")
    
    except Exception as e:
        logger.error(f"Error in debug_calendar: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)[:200]}")


@router.message(F.text == "/debug_help")
async def debug_help_handler(message: Message):
    """
    /debug_help - Show available debug commands
    Admin only command
    """
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return
    
    report = """🔍 <b>ДОСТУПНЫЕ ДИАГНОСТИЧЕСКИЕ КОМАНДЫ</b>

/debug_config - Полная проверка конфигурации
  Проверяет все переменные окружения, доступ к Google Sheets и Calendar

/debug_sheets - Диагностика Google Sheets
  Показывает информацию о листах и структуре документа

/debug_calendar - Диагностика Google Calendar
  Показывает информацию о календаре и ближайшие события

/debug_help - Эта справка

<b>📝 Примечания:</b>
• Команды доступны только администраторам
• Результаты логируются для аудита
• Используйте для диагностики проблем с доступом к API
"""
    
    await message.answer(report, parse_mode="HTML")
