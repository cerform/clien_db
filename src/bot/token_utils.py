"""Utilities for fetching and masking Telegram bot token safely.

This centralizes token fetching logic so all places use the same precedence
and logging behavior (env -> secret manager -> config). It also provides a
masking helper so token values are never logged in full.
"""
from typing import Optional
import os
import logging

from src.core.config_manager import get_secret

logger = logging.getLogger(__name__)


def mask_token(tok: Optional[str]) -> str:
    """Return a short masked summary of a token for safe logging.

    Examples: "len=46 prefix='123456:ABC'"
    """
    if not tok:
        return "<missing>"
    t = tok.strip()
    prefix = t[:12]
    return f"len={len(t)} prefix={prefix!r}"


def _looks_like_placeholder(tok: str) -> bool:
    """Heuristic to detect common placeholder token values.

    Returns True when token contains words like 'your', 'replace', 'dummy', 'test', 'example',
    or looks unusually short for a real Telegram token.
    """
    if not tok:
        return True
    s = tok.strip().lower()
    # Common placeholder indicators
    for word in ["your", "replace", "dummy", "test", "example", "bot_token"]:
        if word in s:
            return True
    # Telegram tokens are long (>=30) and contain a colon; short values are suspicious
    if len(tok) < 30 or ":" not in tok:
        return True
    return False


def get_bot_token() -> Optional[str]:
    """Fetch bot token using the following precedence:

    1. Environment variable `BOT_TOKEN` (Cloud Run secret mounted as env)
    2. Environment variable `TELEGRAM_BOT_TOKEN`
    3. Secret Manager `TELEGRAM_BOT_TOKEN` (via `get_secret`)
    4. Secret Manager `BOT_TOKEN`
    5. Config value (from `Config.from_env().BOT_TOKEN`)

    The function logs where the token came from (masked), but never prints full token.
    """
    # 1 & 2: explicit env vars (works reliably on Cloud Run when secrets are mapped to env)
    for name in ("BOT_TOKEN", "TELEGRAM_BOT_TOKEN"):
        val = os.getenv(name)
        if val:
            if _looks_like_placeholder(val):
                logger.warning(f"⚠️ Value in env var {name} looks like a placeholder; ignoring")
            else:
                logger.info(f"🔑 Using token from env var {name}: {mask_token(val)}")
                return val.strip()

    # 3 & 4: try Secret Manager via config manager helper
    try:
        val = get_secret("TELEGRAM_BOT_TOKEN")
        if val:
            if _looks_like_placeholder(val):
                logger.warning("⚠️ TELEGRAM_BOT_TOKEN in Secret Manager looks like a placeholder; ignoring")
            else:
                logger.info(f"🔑 Using token from Secret Manager TELEGRAM_BOT_TOKEN: {mask_token(val)}")
                return val.strip()
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Failed to read TELEGRAM_BOT_TOKEN from Secret Manager: {e}")

    try:
        val = get_secret("BOT_TOKEN")
        if val:
            if _looks_like_placeholder(val):
                logger.warning("⚠️ BOT_TOKEN in Secret Manager looks like a placeholder; ignoring")
            else:
                logger.info(f"🔑 Using token from Secret Manager BOT_TOKEN: {mask_token(val)}")
                return val.strip()
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Failed to read BOT_TOKEN from Secret Manager: {e}")

    # 5: fallback to Config.from_env (keeps existing behaviour)
    try:
        from src.config.config import Config
        cfg = Config.from_env()
        if cfg.BOT_TOKEN:
            if _looks_like_placeholder(cfg.BOT_TOKEN):
                logger.warning("⚠️ BOT_TOKEN in config looks like a placeholder; ignoring")
            else:
                logger.info(f"🔑 Using token from Config: {mask_token(cfg.BOT_TOKEN)}")
                return cfg.BOT_TOKEN.strip()
    except Exception:
        pass

    logger.warning("⚠️ No Telegram bot token found in env/secret/config")
    return None
