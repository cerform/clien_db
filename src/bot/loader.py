from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging

logger = logging.getLogger(__name__)

# Global instances
bot: Bot = None
dp: Dispatcher = None

async def init_bot(token: str):
    """Initialize bot instance"""
    global bot, dp
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    logger.info("Bot initialized")
    return bot, dp

def get_bot() -> Bot:
    """Get bot instance"""
    if bot is None:
        raise RuntimeError("Bot not initialized. Call init_bot() first")
    return bot

def get_dispatcher() -> Dispatcher:
    """Get dispatcher instance"""
    if dp is None:
        raise RuntimeError("Dispatcher not initialized. Call init_bot() first")
    return dp
