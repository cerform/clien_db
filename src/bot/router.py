from aiogram import Dispatcher
from src.bot.handlers import client_handlers, language_handler, admin_handlers

def register_handlers(dp: Dispatcher):
    """Register all handlers in proper order"""
    # Language handler first (for language selection)
    language_handler.setup(dp)
    
    # Admin handlers (must be before client handlers for priority)
    admin_handlers.setup(dp)
    
    # Client handlers with full Google Calendar sync
    client_handlers.setup(dp)
