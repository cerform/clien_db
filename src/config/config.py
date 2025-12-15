import os
import logging
from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    BOT_TOKEN: str
    USE_WEBHOOK: bool
    WEBHOOK_URL: str
    PORT: int
    GOOGLE_CREDENTIALS_PATH: str
    GOOGLE_TOKEN_PATH: str
    SPREADSHEET_ID: str
    MASTER_CALENDAR_ID: str
    DEFAULT_TIMEZONE: str
    ADMIN_USER_IDS: List[int]
    ENV: str
    OPENAI_API_KEY: str
    DEFAULT_SLOT_DURATION: int
    AI_ONLY_MODE: bool
    ENABLE_LLM: bool

    @staticmethod
    def from_env():
        # Get project root directory (where .env file is)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Helper to convert relative paths to absolute
        def to_absolute_path(path: str) -> str:
            if not path or os.path.isabs(path):
                return path
            return os.path.join(project_root, path)
        
        return Config(
            BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN", ""),
            USE_WEBHOOK=os.getenv("USE_WEBHOOK", "true").lower() in ("1","true","yes"),
            WEBHOOK_URL=os.getenv("WEBHOOK_URL", ""),
            PORT=int(os.getenv("PORT", "8080")),
            GOOGLE_CREDENTIALS_PATH=to_absolute_path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")),
            GOOGLE_TOKEN_PATH=to_absolute_path(os.getenv("GOOGLE_TOKEN_PATH", "token.json")),
            SPREADSHEET_ID=os.getenv("SPREADSHEET_ID", ""),
            MASTER_CALENDAR_ID=os.getenv("MASTER_CALENDAR_ID", ""),
            DEFAULT_TIMEZONE=os.getenv("DEFAULT_TIMEZONE", "Asia/Jerusalem"),
            # Accept comma or semicolon separated values for ADMIN_USER_IDS
            ADMIN_USER_IDS=[int(x.strip()) for x in __import__('re').split('[,;]', os.getenv("ADMIN_USER_IDS", "")) if x.strip()],
            ENV=os.getenv("ENV", "production"),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
                        DEFAULT_SLOT_DURATION=int(os.getenv("DEFAULT_SLOT_DURATION", "120")),
                        AI_ONLY_MODE=os.getenv("AI_ONLY_MODE", "false").lower() in ("1","true","yes"),
                        ENABLE_LLM=os.getenv("ENABLE_LLM", "false").lower() in ("1","true","yes"),
        )

    def validate(self):
        """Validate critical config values and raise ValueError if critical missing"""
        missing = []
        if not self.BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
        # If LLM is explicitly enabled, require OPENAI_API_KEY in production
        if self.ENABLE_LLM and not self.OPENAI_API_KEY:
            if (self.ENV or '').lower() == 'production':
                raise ValueError('ENABLE_LLM is true but OPENAI_API_KEY is missing in production')
            else:
                logging.getLogger(__name__).warning(
                    'ENABLE_LLM is true but OPENAI_API_KEY is missing; continuing in non-production mode'
                )
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
