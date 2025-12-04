#!/usr/bin/env python3
"""
Минимальный тест webhook сервера
"""
import asyncio
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health(request):
    return web.Response(text='OK', status=200)

async def main():
    app = web.Application()
    app.router.add_get('/health', health)
    app.router.add_get('/', health)
    
    logger.info("Starting test server on port 8080")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("✅ Server started successfully")
    
    # Держим сервер запущенным
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
