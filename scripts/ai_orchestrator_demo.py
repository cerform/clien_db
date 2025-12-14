"""
Demo script: Use this to run local orchestrator functions without the bot
Assumes that env vars (GOOGLE_*, BOT_TOKEN, OPENAI_API_KEY) are set.
This is a quick debug utility.
"""

import asyncio
from src.config.env_loader import load_env
from src.config.config import Config
from src.services.ai_dialog_engine import AIDialogEngine, UserRole
from src.services.ai_orchestrator import AIOrchestrator


def run_demo():
    load_env()
    cfg = Config.from_env()
    engine = AIDialogEngine(api_key=cfg.OPENAI_API_KEY)
    orc = AIOrchestrator(engine)

    async def _demo():
        # try listing masters as admin
        res = await orc._execute_action('get_all_masters', {}, user_id=1, user_role=UserRole.ADMIN)
        print('get_all_masters:', res)

        # try listing available slots for today as client
        res2 = await orc._execute_action('get_calendar_slots', {'start_date': '2025-12-13'}, user_id=11111, user_role=UserRole.CLIENT)
        print('get_calendar_slots:', res2)

    asyncio.get_event_loop().run_until_complete(_demo())


if __name__ == '__main__':
    run_demo()
