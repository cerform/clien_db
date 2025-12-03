"""Master handlers"""
from aiogram import types, Dispatcher
from aiogram.filters import Command
from src.config.env_loader import load_env
from src.config.config import Config
from src.db.sheets_client import SheetsClient
import logging

logger = logging.getLogger(__name__)

def setup(dp: Dispatcher):
    dp.message.register(cmd_agenda, Command(commands=["agenda", "my_agenda"]))

async def cmd_agenda(message: types.Message):
    """Show master's today bookings"""
    load_env()
    cfg = Config.from_env()
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        bookings = sc.read_sheet(cfg.SPREADSHEET_ID, "bookings")
        today_bookings = [b for b in bookings if b.get("status") == "confirmed"]
        if not today_bookings:
            await message.answer("📭 No confirmed bookings today")
            return
        msg = "📅 Today's Bookings:\n" + "\n".join([
            f"{b['slot_start']}-{b['slot_end']}: {b.get('client_id', 'Unknown')}"
            for b in today_bookings[:10]
        ])
        await message.answer(msg)
    except Exception as e:
        await message.answer(f"Error: {str(e)[:100]}")
