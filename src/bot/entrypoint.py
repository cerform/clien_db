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

logger = logging.getLogger(__name__)

class NoSSLVerifyAiohttpSession(AiohttpSession):
    """Custom session that doesn't verify SSL"""
    
    async def create_session(self):
        """Create a client session with SSL verification disabled"""
        # Create a connector that doesn't verify SSL
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = TCPConnector(ssl=ssl_context)
        return ClientSession(connector=connector, timeout=None)

def start_bot(cfg):
    token = cfg.BOT_TOKEN
    if not token:
        raise RuntimeError("BOT_TOKEN not set")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run_bot(cfg, loop))

async def _run_bot(cfg, loop):
    default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    session = NoSSLVerifyAiohttpSession()
    # Manually create the client session with SSL disabled before passing to bot
    session.client = await session.create_session()
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
