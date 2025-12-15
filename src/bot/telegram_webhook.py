import os
import logging
import hashlib
import hmac
from fastapi import APIRouter, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from src.core.config_manager import get_secret
from src.bot.token_utils import get_bot_token, mask_token

logger = logging.getLogger(__name__)

router = APIRouter()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "") or get_secret("WEBHOOK_SECRET")

# Lazy-safe bot/dispatcher initialization. Prefer token from env (BOT_TOKEN) or
# explicitly mapped TELEGRAM_BOT_TOKEN; fall back to Secret Manager or config.
bot = None
dp = None
try:
    token = get_bot_token()
    if token:
        try:
            bot = Bot(token=token)
            dp = Dispatcher()
            # Register handlers
            from src.bot.handlers import admin_handlers, master_handlers, language_handler, inka_handler
            bot_mode = os.getenv('BOT_MODE', 'inka').lower()
            if bot_mode == 'advanced':
                try:
                    from src.bot.handlers import ai_handler
                    dp.include_router(ai_handler.create_ai_router())
                except Exception:
                    dp.include_router(inka_handler.create_inka_router())
            else:
                dp.include_router(inka_handler.create_inka_router())
            admin_handlers.setup(dp)
            master_handlers.setup(dp)
            try:
                language_handler.setup(dp)
            except Exception:
                pass
            logger.info(f"✅ Bot initialized from environment: {mask_token(token)}")
        except Exception as e:
            logger.error(f"Failed to initialize Bot at import time: {e}")
            bot = None
            dp = None
except Exception:
    bot = None
    dp = None


def verify_telegram_webhook(secret_token: str, request_token: str) -> bool:
    """
    Verify Telegram webhook request using secret token
    Telegram sends X-Telegram-Bot-Api-Secret-Token header
    """
    if not secret_token:
        # If no secret configured, skip validation (for backward compatibility)
        return True
    return hmac.compare_digest(secret_token, request_token or "")


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram Bot Webhook Endpoint
    Receives and processes updates from Telegram Bot API

    Security:
    - Validates X-Telegram-Bot-Api-Secret-Token header if WEBHOOK_SECRET is configured
    - Prevents unauthorized webhook calls
    """
    global bot, dp

    # If dispatcher isn't configured yet, attempt lazy initialization using the
    # same token helper. This allows us to recover if secrets became available
    # after process start or a previous init failed.
    if not dp:
        logger.info("Dispatcher not configured - attempting lazy bot initialization")
        try:
            token = get_bot_token()
            if token:
                try:
                    bot = Bot(token=token)
                    dp = Dispatcher()
                    try:
                        from src.bot.handlers import admin_handlers, master_handlers, language_handler, inka_handler
                        bot_mode = os.getenv('BOT_MODE', 'inka').lower()
                        if bot_mode == 'advanced':
                            try:
                                from src.bot.handlers import ai_handler
                                dp.include_router(ai_handler.create_ai_router())
                            except Exception:
                                dp.include_router(inka_handler.create_inka_router())
                        else:
                            dp.include_router(inka_handler.create_inka_router())
                        admin_handlers.setup(dp)
                        master_handlers.setup(dp)
                        try:
                            language_handler.setup(dp)
                        except Exception:
                            pass
                    except Exception:
                        logger.exception("Non-fatal: failed to register one or more handlers during lazy init")
                    logger.info(f"✅ Bot initialized during lazy webhook handling: {mask_token(token)}")
                except Exception as e:
                    logger.error(f"Failed to initialize Bot in webhook handler: {e}")
                    bot = None
                    dp = None
            else:
                logger.warning("No token available during lazy init")
        except Exception as e:
            logger.exception(f"Error during lazy init: {e}")

    if not dp:
        logger.error("Telegram webhook called but dispatcher not configured")
        return {"ok": False, "error": "Bot not configured"}

    # Validate webhook secret token (if configured)
    if WEBHOOK_SECRET:
        telegram_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not verify_telegram_webhook(WEBHOOK_SECRET, telegram_secret):
            logger.warning(f"Invalid webhook secret token from IP: {request.client.host if request.client else 'unknown'}")
            raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        data = await request.json()
        data = data or {}
        # Try to extract short summary for better logging (avoid PII)
        summary = {}
        if 'message' in data:
            m = data['message']
            summary = {
                'update_type': 'message',
                'from_id': (m.get('from') or {}).get('id'),
                'chat_id': (m.get('chat') or {}).get('id'),
                'text': (m.get('text') or '')[:200]
            }
        elif 'callback_query' in data:
            cq = data['callback_query']
            summary = {
                'update_type': 'callback_query',
                'from_id': (cq.get('from') or {}).get('id'),
                'chat_id': ((cq.get('message') or {}).get('chat') or {}).get('id'),
                'data': (cq.get('data') or '')[:200]
            }
        else:
            summary = {'update_type': 'unknown'}

        try:
            update = types.Update(**data)
        except Exception as e:
            # If Update validation fails (missing optional fields in test payloads),
            # treat as non-fatal and return OK so Telegram does not retry.
            logger.warning(f"Malformed update payload received; skipping processing: {e}")
            return {"ok": True}

        try:
            await dp.feed_update(bot=bot, update=update)
        except Exception as inner_e:
            # Log handler-level errors with update summary for debugging
            logger.exception(f"Error while processing update (summary={summary}): {inner_e}")
            # If Telegram API returned 'chat not found' (user blocked bot / invalid chat), log as INFO
            text = str(inner_e)
            if 'chat not found' in text.lower() or 'bad request: chat not found' in text.lower():
                logger.warning(f"Telegram API returned chat not found for update summary={summary}: {inner_e}")
            # swallow the exception to avoid 5xx responses (Telegram will not retry on 200)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        # Return 200 even on error to prevent Telegram from retrying
        return {"ok": False, "error": "Internal error processing update"}
