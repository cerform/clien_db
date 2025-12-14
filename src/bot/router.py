from aiogram import Dispatcher
from src.bot.handlers import language_handler, admin_handlers, inka_handler, edit_handlers, ai_handler
from src.config.config import Config
from src.config.env_loader import load_env

def register_handlers(dp: Dispatcher):
    """Register all handlers in proper order"""
    # Language handler first (for language selection)
    language_handler.setup(dp)

    # Admin handlers (must be before client handlers for priority)
    admin_handlers.setup(dp)

    # Edit handlers for CRUD operations (admin only) and INKA bot for normal mode
    # In AI-only mode (no buttons/menus) register only the AI routes
    try:
        load_env()
        cfg = Config.from_env()
        if cfg.AI_ONLY_MODE:
            # AI-only: register admin handlers and the AI router
            admin_handlers.setup(dp)
            dp.include_router(inka_handler.create_inka_router())
            dp.include_router(ai_handler.create_ai_router())
            return
    except Exception:
        # proceed with default registration
        pass

    # Default behavior: register all handlers
    # Admin handlers (must be before client handlers for priority)
    admin_handlers.setup(dp)

    # Edit handlers for CRUD operations (admin only)
    edit_handlers.setup(dp)

    # INKA as the default client handler (rule-based, unified assistant)
    # Use INKA as a universal handler and do not register the UI-driven client_handlers
    dp.include_router(inka_handler.create_inka_router())
