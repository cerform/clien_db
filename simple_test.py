#!/usr/bin/env python3
"""
Простейший webhook тест с ботом
"""
import asyncio
import logging
import os
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("1. Starting...")
        
        from aiogram import Bot
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        logger.info(f"2. Token: {token[:10]}...")
        
        bot = Bot(token=token)
        logger.info("3. Bot created")
        
        app = web.Application()
        
        async def health(request):
            return web.Response(text='OK')
        
        app.router.add_get('/health', health)
        logger.info("4. Routes added")
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        port = 8080
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"✅ Server started on port {port}")
        logger.info("Waiting for requests...")
        
        await asyncio.sleep(60)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
