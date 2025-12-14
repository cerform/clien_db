import asyncio
import logging
import ssl
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import TCPConnector, ClientSession
from src.bot.router import register_handlers
from src.db.cloudsql_client import init_cloudsql_client
from src.db.repositories.admin_messages_repo import AdminMessagesRepo
from src.db.db_factory import init_db_factory, get_db_factory
from src.db.init_postgres import init_database

logger = logging.getLogger(__name__)

# Global repository instances
admin_messages_repo = None
db_factory = None

# PRODUCTION: SSL verification enabled by default (using standard AiohttpSession)
# For development with self-signed certificates, you can enable the NoSSL class below
#
# class NoSSLVerifyAiohttpSession(AiohttpSession):
#     """Custom session that doesn't verify SSL - DEVELOPMENT ONLY"""
#
#     async def create_session(self):
#         """Create a client session with SSL verification disabled"""
#         ssl_context = ssl.create_default_context()
#         ssl_context.check_hostname = False
#         ssl_context.verify_mode = ssl.CERT_NONE
#         connector = TCPConnector(ssl=ssl_context)
#         return ClientSession(connector=connector, timeout=None)

def start_bot(cfg):
    token = cfg.BOT_TOKEN
    if not token:
        raise RuntimeError("BOT_TOKEN not set")

    # Initialize database (PostgreSQL or Sheets)
    global admin_messages_repo, db_factory
    import os
    use_postgres = bool(os.getenv("DATABASE_URL"))

    logger.info(f"Database mode: {'PostgreSQL' if use_postgres else 'Google Sheets'}")

    if use_postgres:
        try:
            # Initialize PostgreSQL schema
            logger.info("Initializing PostgreSQL database...")
            init_result = init_database()
            if init_result:
                logger.info("✅ PostgreSQL schema ready")
            else:
                logger.warning("⚠️ PostgreSQL initialization failed")

            # Initialize database factory
            db_factory = init_db_factory(use_postgres=True)
            admin_messages_repo = db_factory.get_admin_messages_repo()
            logger.info("✅ Database factory initialized (PostgreSQL mode)")
        except Exception as e:
            logger.error(f"❌ PostgreSQL initialization failed: {e}")
            logger.info("Falling back to Google Sheets mode")
            use_postgres = False

    if not use_postgres:
        try:
            # Initialize Sheets-based factory
            db_factory = init_db_factory(use_postgres=False)
            logger.info("✅ Database factory initialized (Google Sheets mode)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database factory: {e}")
            raise

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run_bot(cfg, loop))

def get_admin_messages_repo():
    """Get global admin messages repository instance"""
    return admin_messages_repo

def get_db_factory_instance():
    """Get global database factory instance"""
    return db_factory

async def _run_bot(cfg, loop):
    default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    # PRODUCTION: Use standard session with SSL verification enabled
    session = AiohttpSession()
    bot = Bot(token=cfg.BOT_TOKEN, default=default_properties, session=session)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    register_handlers(dp)
    if cfg.USE_WEBHOOK and cfg.WEBHOOK_URL:
        logger.info("Webhook mode")
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(cfg.WEBHOOK_URL)
        while True:
            await asyncio.sleep(3600)
    else:
        logger.info("Polling mode")
        try:
            await dp.start_polling(bot)
        finally:
            await bot.session.close()
