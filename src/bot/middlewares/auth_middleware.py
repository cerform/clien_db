from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Any, Callable, Dict
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """Middleware for user authentication"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Any],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Process message"""
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
