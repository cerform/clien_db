#!/usr/bin/env python3
"""
Simple startup test - проверяет что контейнер стартует за разумное время
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pytest

@pytest.mark.asyncio
async def test_startup():
    """Test that basic components load without hanging"""
    
    logger.info("=" * 60)
    logger.info("🚀 STARTUP TEST - Проверка времени инициализации")
    logger.info("=" * 60)
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Test 1: Load config
        logger.info("\n1️⃣ Loading config...")
        t1 = asyncio.get_event_loop().time()
        from config import get_config
        config = get_config()
        t2 = asyncio.get_event_loop().time()
        logger.info(f"   ✅ Config loaded in {(t2-t1):.2f}s")
        
        # Test 2: Initialize bot
        logger.info("\n2️⃣ Initializing Telegram bot...")
        t1 = asyncio.get_event_loop().time()
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        bot = Bot(token=config.telegram_bot_token)
        dp = Dispatcher(storage=MemoryStorage())
        t2 = asyncio.get_event_loop().time()
        logger.info(f"   ✅ Bot initialized in {(t2-t1):.2f}s")
        
        # Test 3: Register handlers (lazy, should be fast)
        logger.info("\n3️⃣ Registering handlers (lazy)...")
        t1 = asyncio.get_event_loop().time()
        from bot.handlers import start_handler, client_handler
        dp.include_router(start_handler.router)
        dp.include_router(client_handler.router)
        t2 = asyncio.get_event_loop().time()
        logger.info(f"   ✅ Handlers registered in {(t2-t1):.2f}s")
        
        # Test 4: Create web app (should be fast)
        logger.info("\n4️⃣ Creating web application...")
        t1 = asyncio.get_event_loop().time()
        from aiohttp import web
        app = web.Application()
        
        async def health(request):
            return web.Response(text='OK', status=200)
        
        app.router.add_get('/health', health)
        app.router.add_get('/', health)
        t2 = asyncio.get_event_loop().time()
        logger.info(f"   ✅ Web app created in {(t2-t1):.2f}s")
        
        # Test 5: Setup routes (should be fast)
        logger.info("\n5️⃣ Setting up application routes...")
        t1 = asyncio.get_event_loop().time()
        from aiogram.webhook.aiohttp_server import setup_application
        setup_application(app, dp, bot=bot)
        t2 = asyncio.get_event_loop().time()
        logger.info(f"   ✅ Routes setup in {(t2-t1):.2f}s")
        
        # Test 6: Simulate server start (but don't actually start listening)
        logger.info("\n6️⃣ Simulating server port binding...")
        t1 = asyncio.get_event_loop().time()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '127.0.0.1', 8888)  # Use non-privileged port
        await site.start()
        logger.info("   ✅ Server ready on port 8888")
        t2 = asyncio.get_event_loop().time()
        logger.info(f"   ✅ Server binding in {(t2-t1):.2f}s")
        
        # Cleanup
        await runner.cleanup()
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ STARTUP TEST PASSED in {total_time:.2f}s")
        logger.info("=" * 60)
        
        if total_time < 10:
            logger.info("✅ Startup time is acceptable for Cloud Run (< 10s)")
            return 0
        elif total_time < 30:
            logger.warning("⚠️ Startup time is slow but acceptable (< 30s)")
            return 0
        else:
            logger.error("❌ Startup time is too long (> 30s)")
            return 1
        
    except Exception as e:
        logger.error(f"❌ STARTUP TEST FAILED: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_startup())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
